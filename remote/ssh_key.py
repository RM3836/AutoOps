"""
AutoOps SSH密钥认证模块
功能：密钥登录 / sudo提权 / SFTP文件传输 / 目录列表
技术栈：Paramiko
来自课程实验：06batch/paramiko_key.py, paramiko_sftp.py, paramiko_sudo.py
"""

import paramiko
import logging

logger = logging.getLogger("autoops.ssh_key")


class SSHKeyAuth:
    """SSH密钥认证管理器类
    支持RSA密钥登录、sudo提权执行、SFTP文件传输。
    相比密码登录更安全，适合企业环境。
    """

    @staticmethod
    def connect_with_key(hostname, port, username, key_path):
        """使用RSA密钥文件建立SSH连接。
        Args:
            hostname (str): 目标主机
            port (int): SSH端口
            username (str): 用户名
            key_path (str): 私钥文件路径（如 ~/.ssh/id_rsa）
        Returns:
            paramiko.SSHClient: SSH连接对象
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            private_key = paramiko.RSAKey.from_private_key_file(key_path)
            ssh.connect(hostname=hostname, port=port, username=username, pkey=private_key)
            return ssh
        except Exception as e:
            logger.error(f"密钥认证失败 {hostname}: {e}")
            raise

    @staticmethod
    def exec_with_sudo(hostname, port, username, password, command):
        """sudo提权执行命令（适用于非root用户执行特权操作）。
        Args:
            hostname, port, username, password: SSH连接参数
            command (str): 要执行的命令
        Returns:
            str: 命令执行结果
        """
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=hostname, port=port, username=username, password=password)
            stdin, stdout, stderr = ssh.exec_command(f"sudo -S {command}")
            stdin.write(f"{password}\n")
            stdin.flush()
            result = stdout.read().decode("utf-8", errors="ignore")
            error = stderr.read().decode("utf-8", errors="ignore")
            ssh.close()
            return result or error
        except Exception as e:
            logger.error(f"sudo执行失败 {hostname}: {e}")
            return f"[错误] {str(e)}"

    @staticmethod
    def sftp_upload(hostname, port, username, password, local_path, remote_path):
        """SFTP上传文件。
        Args:
            hostname, port, username, password: 连接参数
            local_path (str): 本地文件路径
            remote_path (str): 远程目标路径
        Returns:
            bool: 上传是否成功
        """
        try:
            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.put(local_path, remote_path)
            sftp.close()
            transport.close()
            return True
        except Exception as e:
            logger.error(f"SFTP上传失败: {e}")
            return False

    @staticmethod
    def sftp_download(hostname, port, username, password, remote_path, local_path):
        """SFTP下载文件。
        Args:
            hostname, port, username, password: 连接参数
            remote_path (str): 远程文件路径
            local_path (str): 本地保存路径
        Returns:
            bool: 下载是否成功
        """
        try:
            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            sftp.get(remote_path, local_path)
            sftp.close()
            transport.close()
            return True
        except Exception as e:
            logger.error(f"SFTP下载失败: {e}")
            return False

    @staticmethod
    def sftp_listdir(hostname, port, username, password, remote_path="/"):
        """SFTP列出远程目录内容。
        Args:
            hostname, port, username, password: 连接参数
            remote_path (str): 远程目录路径，默认根目录
        Returns:
            list: 文件名列表
        """
        try:
            transport = paramiko.Transport((hostname, port))
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            files = sftp.listdir(remote_path)
            sftp.close()
            transport.close()
            return files
        except Exception as e:
            logger.error(f"SFTP列目录失败: {e}")
            return [f"[错误] {str(e)}"]
