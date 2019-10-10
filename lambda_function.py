﻿# -*- coding: utf-8 -*-
"""
@author: Denis W. Slapelis
"""

import json
import boto3
from botocore.vendored import requests
from bs4 import BeautifulSoup

from boto3.dynamodb.conditions import Key


def lambda_handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    dynamoTable = dynamodb.Table('tb_legal_process')
    html = requests.get(event['url'])

    result = getProcessInfo(html.text)
    
    response = dynamoTable.get_item(Key = {
        'NumeroProcesso': result['NumeroProcesso']
    })
    
    if("Item" not in response):
        dynamoTable.put_item(Item = result)

    return {
        'statusCode': 200,
        'result': json.dumps(result)
    }


def getProcessInfo(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find('table', {'class': 'secaoFormBody', 'id': ''})
    partsTable = soup.find('table', {'id': 'tablePartesPrincipais'})
    movementsTable = soup.find('tbody', {'id': 'tabelaUltimasMovimentacoes'})

    info = getGenericInfo(table)
    parts = getProcessParts(partsTable)
    lastMov = getLastMovement(movementsTable)

    result = {
            'NumeroProcesso': info['numProcess'],
            'ValorCausa': info['valor'],
            'Classe': info['classe'],
            'Juiz': info['juiz'],
            'PartesProcesso': parts,
            'UltimaMovimentacao': lastMov
            }

    return result

def getGenericInfo(table):
    result = []
    getValue = 'false'
    labels = ['Processo:', 'Classe:', 'Juiz:', 'Valor da ação:', 'Valor da aÃ§Ã£o:']

    for item in table.findAll('td'):
        if(item.find('label') and item.find('label').get_text() in labels):
            getValue = 'true'
        elif(item.find('span') and getValue == 'true'):
            string = ''
            for span in item.findAll('span'):
                text = span.get_text().strip()
                if(string != text):
                    string += text
            result.append(string)
            getValue = 'false'

    return {'numProcess': formatString(result[0]),
            'valor': formatString(result[3]),
            'classe': formatString(result[1]),
            'juiz': formatString(result[2])
            }

def getProcessParts(table):
    result = []
    part = ''
    i = 1

    for item in table.findAll('td'):
        part += formatString(item.get_text())
        if(i % 2 == 0):
            result.append(part)
            part = ''
        i+=1
    return result

def getLastMovement(table):
    item = table.find_all('td')
    return {'date': formatString(item[0].get_text()),
            'mov': formatString(item[2].get_text())}

def formatString(string):
    return formatSpecialChar(string.replace('\n', ' ').replace('\t', ' ').replace('\xa0', ' ').replace('  ', ' ').strip())

def formatSpecialChar(string):
    return string.replace('Ã£', 'ã').replace('Ã¡', 'á').replace('Ã§', 'ç').replace('Ãº', 'ú').replace('Ã\\x', 'í')
