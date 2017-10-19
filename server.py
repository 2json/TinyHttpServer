# coding: utf-8
from socket import *
from multiprocessing import Process
import sys, re, time

class WSGIServer(object):
    address_family = AF_INET
    socket_type = SOCK_STREAM
    request_queue = 5
    server_name = '127.0.0.1'
    document_dir = './'

    def __init__(self, server_address):
        self.socket = socket(self.address_family, self.socket_type)
        self.socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.socket.bind(server_address)
        self.socket.listen(self.request_queue)
        self.server_port = server_address[1]
    
    def server_start(self):
        while True:
            self.client_socket, client_addr = self.socket.accept()
            client_process = Process(target = self.handle_request, args = (self.client_socket, ))
            client_process.start()
            self.client_socket.close()

    def handle_request(self, client_socket):
        self.recv_data = client_socket.recvfrom(1024)[0]
        request_header_line = self.recv_data.splitlines()
        for line in request_header_line:
            print line
        
        http_method = request_header_line[0]
        filename = re.match(r"[^/]+ (/[^ ]*)", http_method).group(1)

        if filename[-3:] != '.py':
            if filename == '/':
                filename = self.document_dir + 'index.html'
            else:
                filename = self.document_dir + filename
            
            try:
                f = open(filename)
            except IOError:
                response_header = 'HTTP/1.1 404 not found\r\n'
                response_header += '\r\n'
                response_body = 'NOT FOUNDED'
            else:
                response_header = 'HTTP/1.1 200 ok\r\n'
                response_header +='\r\n'
                response_body = f.read()
                f.close()
            finally:
                client_socket.send(response_header + response_body)
                client_socket.close()
        else:
            env = {}
            body_content = self.application(env, self.start_response)
            self.finish_response(body_content)
    
    def application(self, application):
        self.application = application
    
    def start_response(self, status, response_headers):
        server_headers = [
            ('Date', time.ctime()),
            ('Server', 'WSGIServer 1.0')
        ]

        self.headers = [
            status,
            response_headers + server_headers
        ]
    
    def finish_response(self, body_content):
        try:
            status, headers = self.headers
            response_header = 'HTTP/1.1 {status}\r\n'.format(status = status)
            for header in headers:
                response_header += '{0}: {1}\r\n'.format(*header)
            response_header += '\r\n'
            
            for data in body_content:
                response_header += data
            self.client_socket.send(response_header)
        finally:
            self.client_socket.close()

