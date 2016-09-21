import phantom.rules as phantom
import json
from datetime import datetime, timedelta

##############################
# Start - Global Code Block
"""
The investigative Playbook queries a number of external reputation and intelligence services in order to enrich events coming from your data source.  By selecting this Playbook you will be guided through the configuration of a number of common IP, file, domain, and URL reputation services next.
"""

import traceback

def asset_configured(action):
    assets = phantom.get_assets(action=action)
    if assets:
        return True
    
    return False

def get_filtered_assets(action, excluded_products=None):
    
    supported_assets = phantom.get_assets(action=action)
    #phantom.debug(supported_assets)
    ret_assets=[]
    
    if not supported_assets:
        return []
    
    if excluded_products:
        excluded_products = [x.lower() for x in excluded_products]
    
    for asset in supported_assets:
        if excluded_products:
            if asset['product_name'].lower() not in excluded_products:
                ret_assets.append(asset['name'])
        else:
            ret_assets.append(asset['name'])
    
    #phantom.debug(ret_assets)
    return ret_assets

def escalate(container):
    phantom.set_severity(container, "high")
    
def deescalate(container):
    phantom.set_severity(container, "low")
    phantom.close(container)
    
# checks across all hash info providers if the hash is bad or not
def is_file_bad(results):
    
    if not results:
        return []
    
    any_success = False
    for result in results:
        if result['status'] == 'success':
            any_success = True
    
    if not any_success:
        return []
    
    # users can override what they think is tha appropriate thershold
    VT_BAD_THRESHOLD = 5 
    RL_BAD_THRESHOLD = 6
    AUTOFOCUS_TAGS_THRESHOLD = 1
    THREATSCAPE_REPORTS_THRESHOLD = 1
    
    ret_data=[]
    
    try:
        ACTION_INDEX=0
        APP_INDEX=1
        STATUS_INDEX=2
        HASH_INDEX=3
        ARTIFACT_ID_INDEX=4

        
        collected = phantom.collect2(action_results=results, 
                                     datapath=["action",                                        #0
                                               "app",                                           #1
                                               "status",                                        #2
                                               "action_result.parameter.hash",                  #3
                                               "action_result.parameter.context.artifact_id",   #4
                                               # Action specific datapaths
                                               
                                               #5 'file reputation' of Reversing Labs and VirusTotal
                                               "action_result.summary.positives",               #5
                                               #6 'file reputation' of ThreatGrid
                                               "action_result.threatgrid.score",                #6
                                               #7  'hunt file' of AutoFocus
                                               "action_result.summary.total_tags_matched",      #7
                                               #8 'hunt file' of ThreatScape
                                               "action_result.summary.reports_matched"          #8
                                               ])                                       
        
        #phantom.debug(collected)
    
        for item in collected:
            ret_item = {}
            ret_item['hash'] = item[HASH_INDEX]
            ret_item['artifact_id'] = item[ARTIFACT_ID_INDEX]

            if item[ACTION_INDEX] == "file reputation" and item[APP_INDEX] == "ReversingLabs" and item[STATUS_INDEX] == "success":
                if item[HASH_INDEX] and item[ARTIFACT_ID_INDEX] and item[5]:
                    ret_item['bad']= item[5] > RL_BAD_THRESHOLD
                    ret_data.append(ret_item)
                    continue
                    
            if item[ACTION_INDEX] == "file reputation" and item[APP_INDEX] == "VirusTotal" and item[STATUS_INDEX] == "success":
                if item[HASH_INDEX] and item[ARTIFACT_ID_INDEX] and item[5]:
                    ret_item['bad']= item[5] > RL_BAD_THRESHOLD
                    ret_data.append(ret_item)
                    continue
            
            if item[ACTION_INDEX] == "hunt file" and item[APP_INDEX] == "AutoFocus" and item[STATUS_INDEX] == "success":
                if item[HASH_INDEX] and item[ARTIFACT_ID_INDEX] and item[7]:
                    ret_item['bad']= item[7] > AUTOFOCUS_TAGS_THRESHOLD
                    ret_data.append(ret_item)
                    continue
                    
            if item[ACTION_INDEX] == "hunt file" and item[APP_INDEX] == "ThreatScape" and item[STATUS_INDEX] == "success":
                if item[HASH_INDEX] and item[ARTIFACT_ID_INDEX] and item[8]:
                    ret_item['bad']= item[8] > THREATSCAPE_REPORTS_THRESHOLD
                    ret_data.append(ret_item)
                    continue                    
            
    except:
        phantom.error("Exception ocurred in parsing results: {}".format(traceback.format_exc()))
        
    return ret_data

# checks across all domain info providers if the domain is bad or not
def is_domain_bad(results):
    
    if not results:
        return []
    
    any_success = False
    for result in results:
        if result['status'] == 'success':
            any_success = True
    
    if not any_success:
        return []
    
    
    ODNS_MALICIOUS = 'MALICIOUS'
    ATS_THREATSCORE = 70
    POSITIVES_THRESHOLD = 5
    ODNS_KP = 'NORTH KOREA'
    DT_KP = 'kp'
    ATS_KP = 'North Korea'
    WHOIS_KP = 'KP'
    
    ret_data=[]
    
    try:
        #phantom.debug("domain investigation results: {}".format(results))
        ACTION_INDEX=0
        APP_INDEX=1
        STATUS_INDEX=2
        DOMAIN_INDEX=3
        ARTIFACT_ID_INDEX=4
        
        collected = phantom.collect2(action_results=results,
                                     datapath=["action",                                           #0
                                               "app",                                              #1
                                               "status",                                           #2
                                               "action_result.parameter.domain",                   #3
                                               "action_result.parameter.context.artifact_id",      #4
                                               # Action specific data paths
                                               #5: 'domain reputation' from OpenDNS Investigate
                                               "action_result.summary.domain_status",              #5
                                               #6: 'domain reputation' from Passive Total
                                               "action_result.summary.being_watched",              #6
                                               #7: 'domain reputation' from ThreatStream
                                               "action_result.data.*.threatscore",                 #7
                                               #8: 'domain reputation' from URLVoid
                                               "action_result.summary.positives",                  #8
                                               #9: 'domain reputation' from VirusTotal
                                               "action_result.summary.detected_urls",              #9
                                               #10: 'hunt domain' from AutoFocus
                                               "action_result.summary.total_tags_matched",         #10    
                                               #11: 'hunt domain' from ThreatScape
                                               "action_result.summary.reports_matched",            #11
                                               #12: 'reverse domain' from DomainTools
                                               "action_result.summary.total_ips",                  #12
                                               #13: 'whois domain' from DomainTools
                                               "action_result.summary.country",                    #13
                                               #14: 'whois domain' from OpenDNSInvestigate
                                               "action_result.data.*.registrantCountry",           #14
                                               #15: 'whois domain' from ThreatStream
                                               "action_result.data.*.contacts.registrant.country", #15
                                               #16: 'whois domain' from Whois
                                               "action_result.summary.country_code"])              #16                         
        

        #phantom.debug(collected)
    
        for item in collected:
            ret_item = {}
            ret_item['domain'] = item[DOMAIN_INDEX]
            ret_item['artifact_id'] = item[ARTIFACT_ID_INDEX]

            
            if item[ACTION_INDEX] == "domain reputation" and item[APP_INDEX] == "OpenDNS Investigate" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[5]:
                    ret_item['bad']= item[5] == ODNS_MALICIOUS
                    ret_data.append(ret_item)
                    continue
                    
            if item[ACTION_INDEX] == "domain reputation" and item[APP_INDEX] == "PassiveTotal" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[6]:
                    ret_item['bad'] = item[6] 
                    ret_data.append(ret_item)
                    continue
            
            if item[ACTION_INDEX] == "domain reputation" and item[APP_INDEX] == "ThreatStream" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[7]:
                    for threatscore in item[7]:
                        if ret_item['bad']:  # checking if the value has been set yet
                            if ret_item['bad'] == False:  # Checking if the threatscore threshold has been already met.  
                                ret_item['bad']= threatscore > ATS_THREATSCORE
                                ret_data.append(ret_item)          
                                continue
                        else:
                            ret_item['bad']= threatscore > ATS_THREATSCORE
                            ret_data.append(ret_item)          
                            continue

            if item[ACTION_INDEX] == "domain reputation" and item[APP_INDEX] == "URLVoid" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[8]:
                    ret_item['bad']= item[8] > POSITIVES_THRESHOLD
                    ret_data.append(ret_item)
                    continue

            if item[ACTION_INDEX] == "domain reputation" and item[APP_INDEX] == "VirusTotal" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[9]:
                    ret_item['bad']= item[9] > POSITIVES_THRESHOLD
                    ret_data.append(ret_item)       
                    continue

            if item[ACTION_INDEX] == "hunt domain" and item[APP_INDEX] == "AutoFocus" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[10]:
                    ret_item['bad']= item[10] > POSITIVES_THRESHOLD
                    ret_data.append(ret_item)
                    continue
                    
            if item[ACTION_INDEX] == "hunt domain" and item[APP_INDEX] == "ThreatScape" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[11]:
                    ret_item['bad']= item[11] > POSITIVES_THRESHOLD
                    ret_data.append(ret_item)   
                    continue

            if item[ACTION_INDEX] == "reverse domain" and item[APP_INDEX] == "DomainTools" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[12]:
                    ret_item['bad']= item[12] > POSITIVES_THRESHOLD
                    ret_data.append(ret_item)   
                    continue
                    
            if item[ACTION_INDEX] == "whois domain" and item[APP_INDEX] == "DomainTools" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[13]:
                    ret_item['bad']= item[13] == DT_KP
                    ret_data.append(ret_item)  
                    continue
                                        
            if item[ACTION_INDEX] == "whois domain" and item[APP_INDEX] == "OpenDNS Investigate" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[14]:
                    for country in item[14]:
                        if ret_item['bad']:  # checking if the value has been set yet
                            if ret_item['bad'] == False:  # Checking if the 'bad' bit has been already met.  
                                ret_item['bad']= item[14] == ODNS_KP
                                ret_data.append(ret_item)          
                                continue
                        else:
                            ret_item['bad']= item[14] == ODNS_KP
                            ret_data.append(ret_item)          
                            continue

            if item[ACTION_INDEX] == "whois domain" and item[APP_INDEX] == "ThreatStream" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[15]:
                    for country in item[15]:
                        if ret_item['bad']:  # checking if the value has been set yet
                            if ret_item['bad'] == False:  # Checking if the 'bad' bit has been already met.  
                                ret_item['bad']= item[15] == ATS_KP
                                ret_data.append(ret_item)          
                                continue
                        else:
                            ret_item['bad']= item[15] == ATS_KP
                            ret_data.append(ret_item)  
                            continue

            if item[ACTION_INDEX] == "whois domain" and item[APP_INDEX] == "Whois" and item[STATUS_INDEX] == "success":
                if item[DOMAIN_INDEX] and item[ARTIFACT_ID_INDEX] and item[16]:
                    ret_item['bad']= item[16] == WHOIS_KP
                    ret_data.append(ret_item)                              
                    continue

    except:
        phantom.error("Exception ocurred in parsing results: {}".format(traceback.format_exc()))
        
    return ret_data

# checks across all url info providers if the hash is bad or not
def is_url_bad(results):

    
    if not results:
        return []
    
    any_success = False
    for result in results:
        if result['status'] == 'success':
            any_success = True
    
    if not any_success:
        return []
    
    GENERAL_THRESHOLD = 5

    ret_data=[]
    
    try:
        ACTION_INDEX=0
        APP_INDEX=1
        STATUS_INDEX=2
        URL_INDEX=3
        ARTIFACT_ID_INDEX=4
        
        
        collected = phantom.collect2(action_results=results,
                                     datapath=["action",                                        #0
                                               "app",                                           #1
                                               "status",                                        #2
                                               "action_result.parameter.url",                   #3
                                               "action_result.parameter.context.artifact_id",   #4
                                                # Action specific datapaths

                                                #5: 'hunt url' of AutoFocus
                                                "action_result.summary.total_tags_matched",     #5
                                                #6: 'hunt url' of ThreatScape                                                
                                                "action_result.summary.reports_matched",        #6
                                                #7: 'url reputation' of VirusTotal
                                                "action_result.summary.positives"])             #7                               

        #phantom.debug(collected)

        for item in collected:
            ret_item = {}
            ret_item['url'] = item[URL_INDEX]
            ret_item['artifact_id'] = item[ARTIFACT_ID_INDEX]

                                                
            if item[ACTION_INDEX] == "hunt url" and item[APP_INDEX] == "AutoFocus" and item[STATUS_INDEX] == "success":
                if item[URL_INDEX] and item[ARTIFACT_ID_INDEX] and item[5]:
                    ret_item['bad']= item[5] > GENERAL_THRESHOLD
                    ret_data.append(ret_item)
                    continue

            if item[ACTION_INDEX] == "hunt url" and item[APP_INDEX] == "ThreatScape" and item[STATUS_INDEX] == "success":
                if item[URL_INDEX] and item[ARTIFACT_ID_INDEX] and item[6]:
                    ret_item['bad']= item[6] > GENERAL_THRESHOLD
                    ret_data.append(ret_item)
                    continue                    

            if item[ACTION_INDEX] == "url reputation" and item[APP_INDEX] == "VirusTotal" and item[STATUS_INDEX] == "success":
                if item[URL_INDEX] and item[ARTIFACT_ID_INDEX] and item[7]:
                    ret_item['bad']= item[7] > GENERAL_THRESHOLD
                    ret_data.append(ret_item)
                    continue             
                    
    except:
        phantom.error("Exception ocurred in parsing results: {}".format(traceback.format_exc()))                    

    return ret_data

# checks across all ip info providers if the hash is bad or not
def is_ip_bad(results):
    
    if not results:
        return []
    
    any_success = False
    for result in results:
        if result['status'] == 'success':
            any_success = True
    
    if not any_success:
        return []
    
    ODNS_MALICIOUS = 'MALICIOUS'
    THREATSCORE_THRESHOLD = 70
    GENERAL_THRESHOLD = 5
    DOMAIN_THRESHOLD = 100
    LOW_KP = 'kp'
    CAP_KP = 'KP'
    
    ret_data=[]
    
    try:
        #phantom.debug("ip investigation results: {}".format(results))
        
        ACTION_INDEX=0
        APP_INDEX=1
        STATUS_INDEX=2
        IP_INDEX=3
        ARTIFACT_ID_INDEX=4
        
        
        collected = phantom.collect2(action_results=results,
                                     datapath=["action",                                                #0
                                               "app",                                                   #1
                                               "status",                                                #2
                                               "action_result.parameter.ip",                            #3
                                               "action_result.parameter.context.artifact_id",           #4
                                               # Action specific datapaths
                                               "action_result.data.*.country_iso_code",                 #5
                                               "action_result.summary.total_tags_matched",              #6
                                               "action_result.summary.reports_matched",                 #7
                                               "action_result.summary.ip_status",                       #8
                                               "action_result.summary.being_watched",                   #9
                                               "action_result.data.*.threatscore",                      #10
                                               "action_result.summary.detected_urls",                   #11
                                               "action_result.data.*.ip_addresses.domain_count",        #12
                                               "action_result.data.*.parsed_whois.networks.*.country",  #13
                                               "action_result.summary.country_code",                    #14
                                               ])                                                  
        

        #phantom.debug(collected)
        

        for item in collected:
            ret_item = {}
            ret_item['ip'] = item[IP_INDEX]
            ret_item['artifact_id'] = item[ARTIFACT_ID_INDEX]
            
            if item[ACTION_INDEX] == "geolocate ip" and item[APP_INDEX] == "GeoIP2" and item[STATUS_INDEX] == "success":
                if item[5]:
                    ret_item['bad']= CAP_KP in item[5]
                    ret_data.append(ret_item)          
                    continue
                                        
            if item[ACTION_INDEX] == "hunt ip" and item[APP_INDEX] == "AutoFocus" and item[STATUS_INDEX] == "success":
                if item[6]:
                    ret_item['bad']= item[6] > GENERAL_THRESHOLD
                    ret_data.append(ret_item)
                    continue
                    
            if item[ACTION_INDEX] == "hunt ip" and item[APP_INDEX] == "ThreatScape" and item[STATUS_INDEX] == "success":
                if item[7]:
                    ret_item['bad']= item[7] > GENERAL_THRESHOLD
                    ret_data.append(ret_item)
                    continue

            if item[ACTION_INDEX] == "ip reputation" and item[APP_INDEX] == "OpenDNS Investigate" and item[STATUS_INDEX] == "success":
                if item[8]:
                    ret_item['bad']= item[8] == ODNS_MALICIOUS
                    ret_data.append(ret_item)
                    continue                    
                    
            if item[ACTION_INDEX] == "ip reputation" and item[APP_INDEX] == "PassiveTotal" and item[STATUS_INDEX] == "success":
                if item[9]:
                    ret_item['bad'] = item[9]
                    ret_data.append(ret_item)
                    continue                    

            if item[ACTION_INDEX] == "ip reputation" and item[APP_INDEX] == "ThreatStream" and item[STATUS_INDEX] == "success":
                if item[10]:
                    for threatscore in item[10]:
                        if ret_item['bad']:  # checking if the value has been set yet
                            if ret_item['bad'] == False:  # Checking if the threatscore threshold has been already met.  
                                ret_item['bad']= threatscore > THREATSCORE_THRESHOLD
                                ret_data.append(ret_item)          
                                continue
                        else:
                            ret_item['bad']= threatscore > THREATSCORE_THRESHOLD
                            ret_data.append(ret_item)          
                            continue                
                            
            if item[ACTION_INDEX] == "ip reputation" and item[APP_INDEX] == "VirusTotal" and item[STATUS_INDEX] == "success":
                if item[11]:
                    ret_item['bad']= item[11] > GENERAL_THRESHOLD
                    ret_data.append(ret_item)
                    continue 

            if item[ACTION_INDEX] == "reverse ip" and item[APP_INDEX] == "DomainTools" and item[STATUS_INDEX] == "success":                    
                if item[12]:
                    for domain_count in item[12]:
                        if ret_item['bad']:  # checking if the value has been set yet
                            if ret_item['bad'] == False:  # Checking if the threatscore threshold has been already met.  
                                ret_item['bad']= domain_count > DOMAIN_THRESHOLD
                                ret_data.append(ret_item)          
                                continue
                        else:
                            ret_item['bad']= domain_count > DOMAIN_THRESHOLD
                            ret_data.append(ret_item)          
                            continue                                                     


            if item[ACTION_INDEX] == "whois ip" and item[APP_INDEX] == "Whois" and item[STATUS_INDEX] == "success":
                if item[14]:
                    ret_item['bad']= item[14] == CAP_KP
                    ret_data.append(ret_item)
                    continue 
                    
    except:
        phantom.error("Exception ocurred in parsing results: {}".format(traceback.format_exc()))
        
    return ret_data

# checks across user information to determine is user is bad
def is_user_bad(results):
    return []

# End - Global Code block
##############################

def on_start(container):
    
    container_data = phantom.collect2(container=container, datapath=['artifact:*.cef.sourceAddress',            #0
                                                                     'artifact:*.cef.destinationAddress',       #1
                                                                     'artifact:*.cef.requestURL',               #2
                                                                     'artifact:*.cef.sourceDnsDomain',          #3
                                                                     'artifact:*.cef.destinationDnsDomain',     #4
                                                                     'artifact:*.cef.destinationUserName',      #5
                                                                     'artifact:*.cef.fileHash',                 #6
                                                                     'artifact:*.id'])                          #7

    # call 'hunt_ip_1' block
    hunt_ip_1(container=container, handle=container_data)
    
    # call 'geolocate_ip_1' block
    geolocate_ip_1(container=container, handle=container_data)
    
    # call 'lookup_ip_1' block
    lookup_ip_1(container=container, handle=container_data)

    # call 'ip_reputation_1' block
    ip_reputation_1(container=container, handle=container_data)
    
    # call 'whois_ip_1' block
    whois_ip_1(container=container, handle=container_data)
    
    # call 'reverse_ip_1' block
    reverse_ip_1(container=container, handle=container_data)

    # call 'domain_reputation' block
    domain_reputation(container=container, handle=container_data)
    
    # call 'hunt_url_1' block
    hunt_url_1(container=container, handle=container_data)
    
    # call 'url_reputation_1' block
    url_reputation_1(container=container, handle=container_data)

    # call 'file_reputation_1' block
    file_reputation_1(container=container, handle=container_data)

    # call 'lookup_domain_1' block
    lookup_domain_1(container=container, handle=container_data)

    # call 'hunt_domain_1' block
    hunt_domain_1(container=container, handle=container_data)
    
    # call 'reverse_domain_1' block
    reverse_domain_1(container=container, handle=container_data)
    
    # call 'whois_domain_1' block
    whois_domain_1(container=container, handle=container_data)

    # call 'get_file_info_1' block
    get_file_info_1(container=container, handle=container_data)
    
    # call 'hunt_file_1' block
    hunt_file_1(container=container, handle=container_data)

    return

def lookup_ip_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets=get_filtered_assets("lookup ip")
    if not assets:
        return
    
    container_data = handle # in collected data, 0th item is source address and 1st item is destination address

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[0]:
            parameters.append({'ip': container_item[0],'context': {'artifact_id': container_item[7]}})
        if container_item[1]:
            parameters.append({'ip': container_item[1],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("lookup ip", parameters=parameters, name="lookup_ip_1", assets=assets)    
    
    return

def lookup_domain_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("lookup domain")
    if not assets:
        return
    
    container_data = handle # 3rd item is source domain and 4th item is destination domain

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[3]: # source domain
            parameters.append({'domain': container_item[3],'type': "",'context': {'artifact_id': container_item[7]}})
        if container_item[4]: # destination domain
            parameters.append({'domain': container_item[4],'type': "",'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("lookup domain", parameters=parameters, name="lookup_domain_1", assets=assets)    
        
    return

def whois_domain_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("whois domain", excluded_products=["ThreatStream"])
    if not assets:
        return
    
    container_data = handle # in collected data, 3rd item is source domain and 4th item is destination domain

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[3]: # source domain
            parameters.append({'domain': container_item[3],'type': "",'context': {'artifact_id': container_item[7]}})
        if container_item[4]: # destination domain
            parameters.append({'domain': container_item[4],'type': "",'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("whois domain", parameters=parameters, name="whois_domain_1", assets=assets)    
        
    return

def domain_reputation(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("domain reputation", ["ThreatStream"])
    if not assets:
        return
    
    container_data = handle # 3rd item is source domain and 4th item is destination domain

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[3]: # source domain
            parameters.append({'domain': container_item[3],'context': {'artifact_id': container_item[7]}})
        if container_item[4]: # destination domain
            parameters.append({'domain': container_item[4],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("domain reputation", parameters=parameters, name="domain_reputation", assets=assets)    
    
    return

def hunt_domain_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("hunt domain")
    if not assets:
        return
    
    container_data = handle # 3rd item is source domain and 4th item is destination domain

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[3]:# source domain
            parameters.append({'domain': container_item[3],'scope': "",'context': {'artifact_id': container_item[7]}})
        if container_item[4]:# destination domain
            parameters.append({'domain': container_item[4],'scope': "",'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("hunt domain", parameters=parameters, name="hunt_domain_1", assets=assets)    
        
    return

def geolocate_ip_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    if not asset_configured("geolocate ip"):
        return
    
    container_data = handle # in collected data, 0th item is source address and 1st item is destination address

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[0]: # source address
            parameters.append({'ip': container_item[0],'context': {'artifact_id': container_item[7]}})
        if container_item[1]: # destination address
            parameters.append({'ip': container_item[1],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("geolocate ip", parameters=parameters, name="geolocate_ip_1")    
    
    return

def whois_ip_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("whois ip")
    if not asset_configured("whois ip"):
        return
    
    container_data = handle # in collected data, 0th item is source address and 1st item is destination address

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[0]: # source address
            parameters.append({'ip': container_item[0],'context': {'artifact_id': container_item[7]}})
        if container_item[1]: # destination address
            parameters.append({'ip': container_item[1],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("whois ip", parameters=parameters, name="whois_ip_1", assets=assets)    
        
    return

def ip_reputation_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("ip reputation", ["ThreatStream"])
    if not assets:
        return
    
    container_data = handle # in collected data, 0th item is source address and 1st item is destination address

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[0]: # source address
            parameters.append({'ip': container_item[0],'context': {'artifact_id': container_item[7]}})
        if container_item[1]: # destination address
            parameters.append({'ip': container_item[1],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("ip reputation", parameters=parameters, name="ip_reputation_1", assets=assets)    
    
    return

def hunt_ip_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("hunt ip")
    if not assets:
        return
    
    container_data = handle # in collected data, 0th item is source address and 1st item is destination address

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[0]: # source address
            parameters.append({'ip': container_item[0],'context': {'artifact_id': container_item[7]}})
        if container_item[1]: # destination address
            parameters.append({'ip': container_item[1],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("hunt ip", parameters=parameters, name="hunt_ip_1", assets=assets)    
    
    return

def hunt_url_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("hunt url")
    if not assets:
        return
    
    container_data = handle # in collected data, 2nd item is request URL

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[2]: # request URL
            parameters.append({'url': container_item[2],'scope': "",'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("hunt url", parameters=parameters, name="hunt_url_1", assets=assets)    
    
    return

def reverse_domain_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets=get_filtered_assets("reverse domain")
    if not assets:
        return
    
    container_data = handle # in collected data, 3rd item is source domain and 4th item is destination domain

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[3]: # source domain
            parameters.append({'domain': container_item[3],'type': "",'context': {'artifact_id': container_item[7]}})
        if container_item[4]: # destination domain
            parameters.append({'domain': container_item[4],'type': "",'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("reverse domain", parameters=parameters, name="reverse_domain_1", assets=assets)    
    
    return

def get_file_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):
    
    unique_file_hashes=[]
    parameters = []
    if handle:
        for data in handle:
            if data['bad'] == False:
                if data['hash'] not in unique_file_hashes:
                    unique_file_hashes.append(data['hash'])
                    parameters.append({'hash': data['hash'],'context': {'artifact_id': data['artifact_id']}})
                    
    if parameters:
        phantom.debug("get file with parameters: {}".format(parameters))
        return
    
        phantom.act("get file", parameters=parameters, assets=['carbonblack'], callback=detonate_file_1, name="get_file_1")    
    
    return

def file_reputation_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("file reputation", excluded_products=["ThreatStream"])
    if not assets:
        return
    
    container_data = handle # 6th item is file hash

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[6]:
            parameters.append({'hash': container_item[6],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("file reputation", parameters=parameters, name="file_reputation_1", callback=decision_1, assets=assets)    

    return

def detonate_url_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):
    
    unique_urls=[]
    parameters = []
    if handle:
        for data in handle:
            if data['bad'] == False:
                if data['url'] not in unique_urls:
                    unique_urls.append(data['url'])
                    parameters.append({'url': data['url'],'context': {'artifact_id': data['artifact_id']}})
    
    if parameters:
        phantom.debug("parameters for detonate file: {}".format(parameters))
        return
    
        phantom.act("detonate url", parameters=parameters, assets=['cuckoo'], name="detonate_url_1")    
    
    return

def url_reputation_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("url reputation")
    if not assets:
        return
    
    container_data = handle # in collected data, 2nd item is request URL

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[2]:
            url=''
            if container_item[2].startswith("http"):
                url=container_item[2]
            else:
                url = "http://"+container_item[2]
            parameters.append({'url': url,'scope': "",'context': {'artifact_id': container_item[7]}})
    if parameters:
        phantom.act("url reputation", parameters=parameters, name="url_reputation_1", assets=assets)    
        
    return

def decision_2(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    if not success or not results:
        return
    
    data = is_url_bad(results)
    
    for item in data:
        if item['bad'] == True:
            escalate(container)
            return # if anyone reporting this as bad, no need to detonate
        
    detonate_url_1(action=action, success=success, container=container, results=results, handle=data)
    
    return

def decision_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    if not success or not results:
        return
    
    data = is_file_bad(results)
    #phantom.debug("In decision_1.. data: {}".format(data))
    for item in data:
        if item['bad'] == True:
            escalate(container)#phantom.set_severity(container, "high")
            return # if anyone reporting this as bad, no need to detonate
        
    get_file_1(action=action, success=success, container=container, results=results, handle=data)

    return

def detonate_file_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):
    
    #phantom.debug('Action: {0} {1}'.format(action['name'], ('SUCCEEDED' if success else 'FAILED')))
    
    # collect data for 'detonate_file_1' call
    results_data_1 = phantom.collect2(container=container, datapath=['get_file_1:action_result.data.*.vault_id', 'get_file_1:action_result.parameter.context.artifact_id'], action_results=results)

    parameters = []
    
    # build parameters list for 'detonate_file_1' call
    for results_item_1 in results_data_1:
        if results_item_1[0]:
            parameters.append({
                'file_name': "",
                'vault_id': results_item_1[0],
                # context (artifact id) is added to associate results with the artifact
                'context': {'artifact_id': results_item_1[1]},
            })

    if parameters:
        phantom.act("detonate file", parameters=parameters, assets=['cuckoo'], name="detonate_file_1", parent_action=action)    
    else:
        phantom.error("'detonate_file_1' will not be executed due to lack of parameters")
    
    return

def reverse_ip_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):
    
    assets = get_filtered_assets("reverse ip")
    
    if not assets:
        return
    
    container_data = handle # in collected data, 0th item is source address and 1st item is destination address

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[0]: # source address
            parameters.append({'ip': container_item[0],'context': {'artifact_id': container_item[7]}})
        if container_item[1]: # destination address
            parameters.append({'ip': container_item[1],'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("reverse ip", parameters=parameters, name="reverse_ip_1", assets=assets)    
    
    return

def get_file_info_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets = get_filtered_assets("get file info", excluded_products=["Carbon Black"])
    if not assets:
        return
    
    # collect data for 'get_file_info_1' call
    container_data = phantom.collect2(container=container, datapath=['artifact:*.cef.fileHash', 'artifact:*.id'])

    parameters = []
    
    # build parameters list for 'get_file_info_1' call
    for container_item in container_data:
        if container_item[0]:
            if len(container_item[0]) == 64:#length of SHA2s
                parameters.append({
                    'hash': container_item[0],
                    # context (artifact id) is added to associate results with the artifact
                    'context': {'artifact_id': container_item[1]},
                })

    if parameters:
        phantom.act("get file info", parameters=parameters, assets=assets, name="get_file_info_1")    
    
    return

def hunt_file_1(action=None, success=None, container=None, results=None, handle=None, filtered_artifacts=None, filtered_results=None):

    assets= get_filtered_assets("hunt file", excluded_products=["Carbon Black", "Carbon Black Protection","CylancePROTECT"])
    if not assets:
        return
    
    container_data = handle # 6th item is file hash

    parameters = []
    
    # build parameters list for 'geolocate_ip_1' call
    for container_item in container_data:
        if container_item[6]:
            parameters.append({'hash': container_item[6],'scope': "",'context': {'artifact_id': container_item[7]}})

    if parameters:
        phantom.act("hunt file", parameters=parameters, name="hunt_file_1", assets=assets)    

    return

def on_finish(container, summary):

    # This function is called after all actions are completed.
    # summary of all the action and/or all detals of actions 
    # can be collected here.

    ip_actions = ['geolocate ip','hunt ip', 'ip reputation', 'lookup ip', 'reverse ip', 'whois ip']
    domain_actions = ['domain reputation', 'hunt domain', 'lookup domain', 'reverse domain', 'whois domain']
    url_actions = ['hunt url', 'url reputation']
    file_actions = ['funt file', 'file reputation']
    
    summary_json = phantom.get_summary()
    if 'result' in summary_json:
        
        for action_result in summary_json['result']:
            
            if 'action_run_id' in action_result:
                
                action_results = phantom.get_action_results(action_run_id=action_result['action_run_id'], result_data=True, flatten=False)
                if action_results:
                
                    if action_results[0]['action'] in ip_actions:
                        data = is_ip_bad(action_results)
                        for item in data:
                            if item['bad'] == True:
                                phantom.debug("{} is a BAD ip".format(item.get("ip","")))
                                escalate(container)
                                return
                        
                    if action_results[0]['action'] in domain_actions:
                        data = is_domain_bad(action_results)
                        for item in data:
                            if item['bad'] == True:
                                phantom.debug("{} is a BAD domain".format(item.get("domain","")))
                                escalate(container)
                                return                        
                        
                    if action_results[0]['action'] in url_actions:
                        data = is_url_bad(action_results)
                        for item in data:
                            if item['bad'] == True:
                                phantom.debug("{} is a BAD url".format(item.get("url","")))
                                escalate(container)
                                return
                    
                    if action_results[0]['action'] in file_actions:
                        data = is_file_bad(action_results)
                        for item in data:
                            if item['bad'] == True:
                                phantom.debug("{} is a BAD file".format(item.get("hash","")))
                                escalate(container)
                                return
    return