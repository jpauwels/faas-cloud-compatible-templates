#!/usr/bin/env python
from flask import Flask, jsonify, request
from waitress import serve
from dataclasses import dataclass
import base64
import os
import time
from function import lambda_function


@dataclass
class Context:
    function_name: str

    def get_remaining_time_in_millis(self):
        return 0


app = Flask(__name__)
hostname = os.getenv('HOSTNAME', 'localhost')


@app.route('/', defaults={'full_path': ''}, methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
@app.route('/<path:full_path>', methods=['GET', 'PUT', 'POST', 'PATCH', 'DELETE'])
def api_gateway_compatible(full_path):
    ''' A Flask path compatible with Amazon AWS API Gateway HTTP API, with payload format v2.0 (https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html).
    '''
    event = {
        'headers': dict(request.headers),
        'isBase64Encoded': False,
        'pathParameters': request.view_args,
        'queryStringParameters': request.args,
        'rawPath': '/' + full_path,
        'rawQueryString': '&'.join(f'{k}={v}' for k, v in request.args.items(multi=True)),
        'requestContext': {
            'domainName': hostname,
            'domainPrefix': hostname.split('.')[0],
            'http': {
                'method': request.method,
                'path': '/' + full_path.rstrip('/'),
                'protocol': request.environ.get('SERVER_PROTOCOL', ''),
            },
            'time': time.strftime('%d/%b/%Y:%X %z'),
            'timeEpoch': round(time.time()),
        },
        # 'multiValueQueryStringParameters': request.args.to_dict(flat=False), # Payload format v1.0
    }
    if request.get_data():
        event['body'] = request.get_data()
        try:
            event['isBase64Encoded'] = base64.b64encode(base64.b64decode(event['body'])) == event['body']
        except base64.binascii.Error:
            event['isBase64Encoded'] = False
    context = Context(
        function_name=request.headers.get('Host', '').split('.')[0],
    )
    res = lambda_function.lambda_handler(event, context)
    if not isinstance(res, dict) or 'body' not in res:
        return jsonify(res)
    return res['body'], res.get('statusCode', 200), tuple(res.get('headers', {'Content-Type': 'application/json'}).items())


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000)
