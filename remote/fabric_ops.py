"""
AutoOps Fabric批量运维模块
功能：批量执行命令 / 批量部署 / 批量文件分发 / sudo提权
技术栈：Fabric（课程核心库第4个）
来自课程实验：06batch/fabric_basic.py, fabric_group1.py, lamp_byfabric.py
"""

import logging
from fabric import Connection
from invoke.exceptions import UnexpectedExit

logger = logging.getLogger("autoops.fabric")


class FabricOps:
    """Fabric批量运维类
    通过Fabric Connection实现多服务器批量操作。
    使用Fabric Python API而非subprocess调用fab命令行。
    """

    @staticmethod
    def run_command(hosts, command, user="root"):
        """在多台服务器上批量执行命令。
        Args:
            hosts (list): 主机IP列表，如 ["192.168.1.10", "192.168.1.11"]
            command (str): 要执行的Linux命令
            user (str): SSH用户名，默认root
        Returns:
            dict: {主机IP: 命令输出}
        """
        results = {}
        for host in hosts:
            try:
                # 使用Fabric Connection连接远程主机
                conn = Connection(host=host, user=user, connect_timeout=10)
                # 执行命令，获取输出
                result = conn.run(command, hide=True, warn=True, timeout=30)
                results[host] = result.stdout.strip() or result.stderr.strip()
                conn.close()
            except UnexpectedExit as e:
                results[host] = f"[退出码{e.result.exited}] {e.result.stderr.strip()}"
            except Exception as e:
                results[host] = f"[错误] {str(e)}"
        return results

    @staticmethod
    def deploy_file(hosts, local_path, remote_path, user="root"):
        """批量分发文件到多台服务器。
        Args:
            hosts (list): 主机IP列表
            local_path (str): 本地文件路径
            remote_path (str): 远程目标路径
            user (str): SSH用户名
        Returns:
            dict: {主机IP: 分发结果}
        """
        results = {}
        for host in hosts:
            try:
                conn = Connection(host=host, user=user, connect_timeout=10)
                # 使用Fabric的put方法上传文件
                conn.put(local_path, remote_path)
                results[host] = "成功"
                conn.close()
            except Exception as e:
                results[host] = f"[错误] {str(e)}"
        return results

    @staticmethod
    def install_package(hosts, package_name, user="root"):
        """批量安装软件包。
        Args:
            hosts (list): 主机IP列表
            package_name (str): 软件包名称
            user (str): SSH用户名
        Returns:
            dict: {主机IP: 安装结果}
        """
        cmd = f"yum install -y {package_name}"
        return FabricOps.run_command(hosts, cmd, user)
