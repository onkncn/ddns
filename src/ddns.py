# -*- coding: utf-8 -*-
# 阿里云DDNS更新工具
# 支持通过环境变量或配置文件配置，自动检测IP变化并更新DNS记录
import os
import sys
import requests
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from alibabacloud_tea_openapi.client import Client as OpenApiClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_openapi_util.client import Client as OpenApiUtilClient
from alibabacloud_tea_console.client import Client as ConsoleClient
from alibabacloud_tea_util.client import Client as UtilClient


def get_ip():
    """
    获取公网IP地址
    使用多个IP检测服务作为备用，提高可靠性
    """
    # IP检测服务列表，按优先级排序
    ip_services = [
        # 服务URL, 是否POST请求, 响应中IP的路径或处理方式
        ('https://api.ipify.org', False, lambda resp: resp.text.strip()),
        ('https://jsonip.com', False, lambda resp: resp.json().get('ip')),
        ('https://api.myip.com', False, lambda resp: resp.json().get('ip')),
        ('https://ipinfo.io/ip', False, lambda resp: resp.text.strip()),
        ('https://ip.seeip.org', False, lambda resp: resp.text.strip())
    ]
    
    for url, is_post, ip_extractor in ip_services:
        try:
            print(f"尝试从 {url} 获取IP...")
            if is_post:
                response = requests.post(url, timeout=5)
            else:
                response = requests.get(url, timeout=5)
            
            response.raise_for_status()  # 检查HTTP响应状态
            
            # 提取IP地址
            ip = ip_extractor(response)
            
            if ip and isinstance(ip, str) and ip.strip():
                print(f"成功获取IP: {ip}")
                return ip.strip()
        except Exception as e:
            print(f"从 {url} 获取IP失败: {str(e)}")
    
    # 如果所有服务都失败，抛出异常
    raise Exception("所有IP检测服务均失败，请检查网络连接")


def load_config(config_file=None) -> Dict[str, Any]:
    """
    加载配置信息
    优先从环境变量读取，其次从配置文件读取，最后使用默认值
    """
    # 默认配置
    config = {
        'access_key_id': '',
        'access_key_secret': '',
        'domain_name': '',
        'rr': '@',
        'record_type': 'A',
        'ttl': 600,
        'ip_file': '/tmp/ddns_current_ip.txt',
        'log_level': 'INFO'
    }
    
    # 从配置文件加载（如果提供）
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                config.update(file_config)
        except Exception as e:
            raise ValueError(f"加载配置文件失败: {str(e)}")
    
    # 从环境变量加载（优先级高于配置文件）
    env_mapping = {
        'access_key_id': 'ALIYUN_ACCESS_KEY_ID',
        'access_key_secret': 'ALIYUN_ACCESS_KEY_SECRET',
        'domain_name': 'DDNS_DOMAIN_NAME',
        'rr': 'DDNS_RR',
        'record_type': 'DDNS_RECORD_TYPE',
        'ttl': 'DDNS_TTL',
        'log_level': 'DDNS_LOG_LEVEL'
    }
    
    for config_key, env_key in env_mapping.items():
        if env_key in os.environ:
            config[config_key] = os.environ[env_key]
    
    # 特殊处理TTL，确保是整数
    if isinstance(config['ttl'], str):
        try:
            config['ttl'] = int(config['ttl'])
        except ValueError:
            raise ValueError(f"TTL必须是整数，当前值: {config['ttl']}")
    
    # 验证必需参数
    required_fields = ['access_key_id', 'access_key_secret', 'domain_name']
    for field in required_fields:
        if not config.get(field):
            raise ValueError(f"缺少必需配置: {field}")
    
    return config


def save_current_ip(ip: str, ip_file: str) -> None:
    """
    保存当前IP到本地文件
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(os.path.abspath(ip_file)), exist_ok=True)
        
        # 保存IP和时间戳
        data = {
            'ip': ip,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(ip_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"保存IP到文件失败: {str(e)}")


def get_saved_ip(ip_file: str) -> Optional[str]:
    """
    从本地文件获取上次保存的IP
    """
    try:
        if os.path.exists(ip_file):
            with open(ip_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('ip')
    except Exception as e:
        print(f"从文件读取IP失败: {str(e)}")
    return None


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> OpenApiClient:
        """
        使用AK&SK初始化账号Client
        @param access_key_id:
        @param access_key_secret:
        @return: Client
        @throws Exception
        """
        config = open_api_models.Config(
            # 必填，您的 AccessKey ID,
            access_key_id=access_key_id,
            # 必填，您的 AccessKey Secret,
            access_key_secret=access_key_secret
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Alidns
        config.endpoint = f'alidns.cn-shanghai.aliyuncs.com'
        return OpenApiClient(config)

    @staticmethod
    def create_api_info(action='UpdateDomainRecord') -> open_api_models.Params:
        """
        API 相关配置
        @param action: API操作名称
        @return: OpenApi.Params
        """
        params = open_api_models.Params(
            # 接口名称,
            action=action,
            # 接口版本,
            version='2015-01-09',
            # 接口协议,
            protocol='HTTPS',
            # 接口 HTTP 方法,
            method='POST',
            auth_type='AK',
            style='RPC',
            # 接口 PATH,
            pathname=f'/',
            # 接口请求体内容格式,
            req_body_type='json',
            # 接口响应体内容格式,
            body_type='json'
        )
        return params
    
    @staticmethod
    def get_domain_record(
        client: OpenApiClient,
        domain_name: str,
        rr: str,
        record_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取域名记录信息
        """
        # 创建API信息
        api_info = Sample.create_api_info(action='DescribeDomainRecords')
        
        # 构建请求参数
        params = {
            'DomainName': domain_name,
            'RRKeyWord': rr,
            'TypeKeyWord': record_type
        }
        
        # 执行请求
        runtime = util_models.RuntimeOptions()
        request = open_api_models.OpenApiRequest(
            query=OpenApiUtilClient.query(params)
        )
        resp = client.call_api(api_info, request, runtime)
        print(resp)
        # 解析响应
        body = resp.get('body')
        if body:
            # 直接从返回值获取记录列表（适配新的返回格式）
            records = body.get('DomainRecords', {}).get('Record', [])
            # 查找匹配的记录
            for record in records:
                if record.get('RR') == rr and record.get('Type') == record_type:
                    return record
                    
            # 如果没有找到匹配的记录，检查是否有错误
            if body.get('Code'):
                # 如果响应中有错误代码，抛出异常
                error_code = body.get('Code')
                error_msg = body.get('Message', str(body))
                raise Exception(f"阿里云API错误: {error_code} - {error_msg}")
        
        return None
    
    @staticmethod
    def update_domain_record(
        client: OpenApiClient,
        record_id: str,
        rr: str,
        record_type: str,
        value: str,
        ttl: int
    ) -> Dict[str, Any]:
        """
        更新域名记录
        """
        try:
            # 创建API信息
            api_info = Sample.create_api_info(action='UpdateDomainRecord')
            
            # 构建请求参数
            params = {
                'RecordId': record_id,
                'RR': rr,
                'Type': record_type,
                'Value': value,
                'TTL': ttl
            }
            
            # 执行请求
            runtime = util_models.RuntimeOptions()
            request = open_api_models.OpenApiRequest(
                query=OpenApiUtilClient.query(params)
            )
            resp = client.call_api(api_info, request, runtime)
            
            return resp
        except Exception as e:
            print(f"更新域名记录失败: {str(e)}")
            raise

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        """
        主函数，执行DDNS更新
        """
        # 解析命令行参数，支持指定配置文件
        config_file = None
        if args:
            config_file = args[0]
        
        try:
            # 加载配置
            config = load_config(config_file)
            
            # 配置日志
            log_level = getattr(logging, config['log_level'].upper(), logging.INFO)
            logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
            logger = logging.getLogger(__name__)
            
            logger.info(f"开始DDNS更新任务 - 域名: {config['domain_name']}, 主机记录: {config['rr']}")
            
            # 尝试从文件获取上次保存的IP
            saved_ip = get_saved_ip(config['ip_file'])
            
            # 获取当前公网IP
            current_ip = get_ip()
            logger.info(f"获取到当前公网IP: {current_ip}")
            
            # 先检查与本地保存的IP是否相同，避免不必要的API调用
            if saved_ip == current_ip:
                logger.info(f"IP未变化（与本地记录相同），无需更新DNS记录 ({current_ip})")
                return
            
            # 创建阿里云客户端
            client = Sample.create_client(config['access_key_id'], config['access_key_secret'])
            
            # 获取现有DNS记录
            try:
                record = Sample.get_domain_record(client, config['domain_name'], config['rr'], config['record_type'])
                if not record:
                    raise ValueError(f"未找到域名记录: {config['rr']}.{config['domain_name']} (类型: {config['record_type']})")
            except Exception as e:
                # 检查是否是凭证相关错误
                if 'InvalidAccessKeyId.NotFound' in str(e) or 'InvalidAccessKeySecret' in str(e):
                    raise ValueError(f"阿里云访问凭证无效: {str(e)}")
                raise
            
            record_id = record.get('RecordId')
            current_record_ip = record.get('Value')
            
            # 检查IP是否变化
            if current_ip == current_record_ip:
                # 虽然DNS记录没变化，但本地保存的IP不同，更新本地记录
                save_current_ip(current_ip, config['ip_file'])
                logger.info(f"IP未变化（与DNS记录相同），已更新本地IP记录 ({current_ip})")
                return
            
            logger.info(f"IP已变化，准备更新DNS记录 - 从 {current_record_ip} 到 {current_ip}")
            
            # 更新DNS记录
            resp = Sample.update_domain_record(client, record_id, config['rr'], config['record_type'], current_ip, config['ttl'])
            
            # 检查更新是否成功
            status_code = resp.get('statusCode')
            if status_code == 200:
                # 更新成功后保存IP到本地文件
                save_current_ip(current_ip, config['ip_file'])
                logger.info(f"DNS记录更新成功 - {config['rr']}.{config['domain_name']} -> {current_ip}")
            else:
                logger.error(f"DNS记录更新失败，状态码: {status_code}")
                logger.error(f"响应内容: {UtilClient.to_jsonstring(resp)}")
                raise Exception(f"DNS记录更新失败，状态码: {status_code}")
                
        except ValueError as e:
            logger.error(f"配置错误: {str(e)}")
            print(f"错误: {str(e)}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"执行DDNS更新时出错: {str(e)}")
            print(f"错误: {str(e)}")
            raise

    # 异步方法暂时移除，避免依赖aiohttp导致的兼容性问题
    # 如需异步功能，请在Python 3.10以下环境使用或等待aiohttp更新支持Python 3.12

if __name__ == '__main__':
    Sample.main(sys.argv[1:])
