"""
AutoOps SSH远程运维模块
功能：SSH远程登录 / 批量执行命令 / 文件上传下载 / 多服务器管理
技术栈：Paramiko
来自课程实验：06batch/paramiko_pwd.py, paramiko_sftp.py, paramiko_sudo.py
"""

import paramiko
import logging

logger = logging.getLogger("autoops.ssh")


class SSHManager:
    """SSH远程运维管理器类
    封装Paramiko库，提供SSH连接、命令执行、文件传输等功能。
    """

    def connect(self, hostname, port, username, password):
        """建立SSH连接。
        Args:
            hostname (str): 目标主机IP或域名
            port (int): SSH端口，默认22
            username (str): 登录用户名
            password (str): 登录密码
        Returns:
            paramiko.SSHClient: SSH连接对象
        Raises:
            paramiko.AuthenticationException: 认证失败
            socket.timeout: 连接超时
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname, port=port, username=username,
                        password=password, timeout=10)
            return ssh
        except paramiko.AuthenticationException:
            logger.error(f"SSH认证失败: {username}@{hostname}")
            raise
        except Exception as e:
            logger.error(f"SSH连接失败 {hostname}: {e}")
            raise

    def exec_command(self, hostname, port, username, password, command):
        """远程执行Linux命令。
        Args:
            hostname (str): 目标主机
            port (int): SSH端口
            username (str): 用户名
            password (str): 密码
            command (str): 要执行的Linux命令
        Returns:
            str: 命令执行结果（stdout + stderr）
        """
        try:
            ssh = self.connect(hostname, port, username, password)
            stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
            result = stdout.read().decode("utf-8", errors="ignore")
            error = stderr.read().decode("utf-8", errors="ignore")
            ssh.close()
            if error.strip():
                return f"[stdout]\n{result}\n[stderr]\n{error}"
            return result
        except Exception as e:
            logger.error(f"SSH执行失败 {hostname}: {e}")
            return f"[错误] {str(e)}"

    def upload_file(self, hostname, port, username, password, local_path, remote_path):
        """SFTP上传文件到远程服务器。
        Args:
            hostname, port, username, password: SSH连接参数
            local_path (str): 本地文件路径
            remote_path (str): 远程目标路径
        Returns:
            tuple: (成功标志, 消息)
        """
        try:
            ssh = self.connect(hostname, port, username, password)
            sftp = ssh.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            ssh.close()
            return True, f"上传成功: {local_path} -> {remote_path}"
        except Exception as e:
            return False, f"上传失败: {str(e)}"

    def download_file(self, hostname, port, username, password, remote_path, local_path):
        """SFTP从远程服务器下载文件。
        Args:
            hostname, port, username, password: SSH连接参数
            remote_path (str): 远程文件路径
            local_path (str): 本地保存路径
        Returns:
            tuple: (成功标志, 消息)
        """
        try:
            ssh = self.connect(hostname, port, username, password)
            sftp = ssh.open_sftp()
            sftp.get(remote_path, local_path)
            sftp.close()
            ssh.close()
            return True, f"下载成功: {remote_path} -> {local_path}"
        except Exception as e:
            return False, f"下载失败: {str(e)}"

    def batch_exec(self, hosts, command):
        """批量执行命令（多服务器统一管理）。
        Args:
            hosts (list): 主机列表，每项为dict: {hostname, port, username, password}
            command (str): 要执行的命令
        Returns:
            dict: {主机标识: 命令结果}
        """
        results = {}
        for h in hosts:
            try:
                key = f"{h['hostname']}:{h.get('port', 22)}"
                results[key] = self.exec_command(
                    h["hostname"], h.get("port", 22),
                    h["username"], h["password"], command
                )
            except Exception as e:
                results[f"{h['hostname']}:{h.get('port',22)}"] = f"[错误] {str(e)}"
        return results
