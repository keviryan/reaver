import boto3
import logging
import sys
from botocore.session import Session
from botocore.config import Config
from time import sleep

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fh = logging.FileHandler('reaver.log')
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


apigw = boto3.client('apigateway', config=Config(retries={'max_attempts': 1}))
cwl = boto3.client('logs')

def get_apis():
    apis = {}
    try:
        response = apigw.get_rest_apis(
            limit=100
        )
        for api in response['items']:
            api_id = api['id']
            api_name = api['name']
            apis[api_name]= api_id
        return apis    
    except:
        raise

def delete_apis(my_apis, apis_to_delete):

    for api_name in apis_to_delete:
        if api_name not in my_apis:
            logger.info("Cannot delete API with name " + api_name + " because it was not found on this account.")


    for api_name, api_id in my_apis.items():
        if api_name in apis_to_delete:
            try:
                apigw.delete_rest_api(
                restApiId=api_id
                )
                logger.info("Deleted {}. Sleeping for 30 seconds.".format(api_name))
                sleep(30)      
            except apigw.exceptions.TooManyRequests:
                logger.error("Throttled after two attempts to delete {}...Sleeping for 10 Seconds and trying again.".format(api_name), exc_info=True)
                sleep(10)
                try:
                    apigw.delete_rest_api(
                        restApiId=api_id
                    )
                    logger.info("Deleted {}".format(api_name))
                except (SystemExit, KeyboardInterrupt):
                    raise
                except:
                    logger.error('Failed to delete {}'.format(api_name), exc_info=True)
                    sleep(10)
                    pass

def get_log_groups(my_apis, apis_to_delete):
    

    for api_name in apis_to_delete:
        if api_name not in my_apis:
            logger.info("Cannot delete log groups for API {} becuase it was not found on this account.".format(api_name))

    api_gw_log_groups = {}
    for api_name, api_id in my_apis.items():
        if api_name in apis_to_delete:
            try:
                response = apigw.get_stages(
                restApiId=api_id
                )
                log_groups = []
                api_gw_log_groups[api_name]= log_groups
                for stage in response['item']:
                    stage_name = (stage['stageName'])
                    log_groups.append("API-Gateway-Execution-Logs_{}/{}".format(api_id, stage_name)) 
            except Exception as e:
                logger.error(e, exc_info=True)
                pass            
    return api_gw_log_groups

def delete_log_groups(log_groups_to_delete):
    
    for api_name, log_groups in log_groups_to_delete.items():
        for log_group in log_groups:
            try:
                response = cwl.delete_log_group(
                    logGroupName=log_group
                )
                logger.info("Log Group {} has been removed".format(log_group))
            except cwl.exceptions.ResourceNotFoundException:
                logger.error("Log Group {} has already been removed or it does not exist".format(log_group))
                pass

def main():

    delete_these = []
    input_file = sys.argv[1]
    with open(input_file, 'r') as i:
        for line in i:
            delete_these.append(line.replace("\n", ""))
    logger.info("APIs to delete: {}".format(delete_these))

    delete_log_groups(get_log_groups(get_apis(), delete_these))
    delete_apis(get_apis(),delete_these)
    
if __name__ == '__main__':
    main()