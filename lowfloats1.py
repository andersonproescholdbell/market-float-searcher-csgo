from steam import SteamClient
from csgo import CSGOClient
from csgo.enums import ECsgoGCMsg
import gevent
import requests
import json
import struct
import sqlite3
import externalLists

def getMarketItems(url, count):
    inspect_list = []
    total_count = count
    loaded = 0
    start = 0
    price_list = []
    while (count >= 100):
        try:
            urlextender = ('/render/?query=&start=%s&count=100&currency=1' % start)
            request = requests.get(url + urlextender)
            data = request.text.split('"listinginfo":')[1].split(',"assets":')[0]
            data = json.loads(data)
            for marketID in data:
                price = int(data[marketID]['converted_price']) + int(data[marketID]['converted_fee'])
                padded = "%03d" % (price,)
                price = padded[0:-2] + '.' + padded[-2:]
                price = float(price)
                link = data[marketID]['asset']['market_actions'][0]['link']
                assetID = data[marketID]['asset']['id']
                inspectlink = link.replace('%assetid%', assetID).replace('%listingid%', marketID)
                inspect_list.append(inspectlink)
                price_list.append(price)
            count = count - 100
            start = start + 100
            loaded = loaded + 100
            print("%s / %s floats loaded, waiting 7 seconds." % (loaded, total_count))
            if (count >= 100):
                gevent.sleep(7)
        except:
            print("Failed collecting data. Retrying...")
            gevent.sleep(7)
        
            
    try:
        if (count < 100 and count != 0):
            urlextender = '/render/?query=&start=%s&count=%s&currency=1' % (start, count)
            request = requests.get(url + urlextender)
            data = request.text.split('"listinginfo":')[1].split(',"assets":')[0]
            data = json.loads(data)
            for marketID in data:
                price = int(data[marketID]['converted_price']) + int(data[marketID]['converted_fee'])
                padded = "%03d" % (price,)
                price = padded[0:-2] + '.' + padded[-2:]
                price = float(price)
                link = data[marketID]['asset']['market_actions'][0]['link']
                assetID = data[marketID]['asset']['id']
                inspectlink = link.replace('%assetid%', assetID).replace('%listingid%', marketID)
                inspect_list.append(inspectlink)
                price_list.append(price)
                fail = 0
    except:
        if (fail != 1):
            fail = 1
            print("Failed collecting data. Retrying...")
        if (fail == 1):
            fail = 0
            print("Failed collecting data. Skipping...")
        
    print("%s floats loaded." % total_count)
    inspect_price_list = [inspect_list, price_list]
    return inspect_price_list

def Get_Item_Data(inspect_list, price_list, cs, wanted, specificity):
    total_links = len(inspect_list)
    n = 0
    error = 0
    while (n < total_links):
        try:
            printed = 0
            current_inspect_link = inspect_list[n]
            price = price_list[n]
            itemcode = current_inspect_link.replace('steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20' ,'').split('A')
            param_m = int(itemcode[0].replace('M',''))
            itemAD = itemcode[1].split('D')
            param_a = int(itemAD[0])
            param_d = int(itemAD[1])
            itemdata = CSGO_Check_Item(param_a, param_d, param_m, cs)
            paintseed = int(itemdata[0].iteminfo.paintseed)
            paintwear = int(itemdata[0].iteminfo.paintwear)
            paintindex = int(itemdata[0].iteminfo.paintindex)
            defindex = str(itemdata[0].iteminfo.defindex)
            skin_name = externalLists.weaponIndex[defindex]
            skin_id = 'ID' + str(paintindex)
            skin_pattern = externalLists.skinIndex[skin_id]
            item_float = float(Get_Float(paintwear))
            print(item_float);
            if (item_float >= wanted and item_float <= (wanted + specificity)):
                print("%s %s     %s     $$ %s      %s" % (skin_name, skin_pattern, item_float, price, current_inspect_link))
            n += 1
            gevent.sleep(1)
        except:
            print("Retrying item...")
            gevent.sleep(1)

def CSGO_Check_Item(param_a, param_d, param_m, cs):
    try:
        cs.send(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockRequest,
            {
                'param_s': 0,
                'param_a': param_a,
                'param_d': param_d,
                'param_m': param_m,
            })
        response = cs.wait_event(ECsgoGCMsg.EMsgGCCStrike15_v2_Client2GCEconPreviewDataBlockResponse, timeout=10)

    except:
        return None

    return response

def Get_Float(paintwear):
    buf = struct.pack('i', paintwear)
    item_float = struct.unpack('f', buf)[0]
    return item_float

def Start():
    url = input("Market url: ")
    count = int(input("Number of items to load: "))
    wanted = float(input("Which float are you aiming for? "))
    specificity = float(input("How much above float are you willing to show? "))
    inspect_price_list = getMarketItems(url, count)
    inspect_list = inspect_price_list[0]
    price_list = inspect_price_list[1]

    print("")
    ready = False
    while (ready == False):
        try:
            print("Try to log in")
            client = SteamClient()
            cs = CSGOClient(client)
            @client.on('logged_on')
            def start_csgo():
                cs.launch()
            @cs.on('ready')
            def gc_ready():
                pass
            client.cli_login()
            ready = True
        except:
            print("There was an error, try again")
    print("Waiting 10 seconds for CSGO to start")
    print("")
    gevent.sleep(10)
    
    Get_Item_Data(inspect_list, price_list, cs, wanted, specificity)

Start()
    
