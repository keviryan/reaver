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

def get_basepaths():
    mapped_domains = {}
    try:
        domain_names = apigw.get_domain_names()
    except:
        logger.error("couldn't get domain names",  exc_info=True)
    for domain in domain_names['items']:
        domain_name = domain['domainName']
        base_path_mappings = []
        mapped_domains[domain_name] = base_path_mappings
        try:
            base_paths = apigw.get_base_path_mappings(domainName=domain_name)
            for base_path in base_paths['items']:
                print(base_path)
                if (base_path['basePath'] == '(none)' or ' '):
                    base_path_mappings.append(tuple((' ', base_path['restApiId'])))
                else:
                    base_path_mappings.append(tuple((base_path['basePath'], base_path['restApiId'])))
        except:
            logger.warn("couldn't get basepath mappings for ",  exc_info=True)
    return(mapped_domains)

def get_log_groups(my_apis, apis_to_delete):
    for api_name in apis_to_delete:
        if api_name not in my_apis:
            logger.warn("Cannot retrieve the log groups for {} becuase it was not found on this account.".format(api_name))

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


def delete_apis(my_apis, apis_to_delete, log_groups, base_path_mappings):

    for api_name in apis_to_delete:
        if api_name not in my_apis:
            logger.warn("Cannot delete API with name " + api_name + " because it was not found on this account.")

    for api_name, api_id in my_apis.items():
        if api_name in apis_to_delete:
            try:
                delete_base_path_mappings(api_id, base_path_mappings)
            except Exception as e:
                logger.error("Cloudn't delete base path mappings", exc_info=True)
            try:
                apigw.delete_rest_api(
                restApiId=api_id
                )
                logger.info("Deleted {}".format(api_name))
                logger.info("Sleeping for 30 seconds")        
                sleep(30)
            except (SystemExit, KeyboardInterrupt):
                    logger.error("SystemExit or KeyboardInterupt")
                    raise
            except apigw.exceptions.BadRequestException:
                    logger.error("Could not delete the API. Ensure there was no issue deleting the basepath mapping", exc_info=True)
                    raise      
            except apigw.exceptions.TooManyRequests:
                logger.error("Throttled after two attempts to delete {}...Sleeping for 10 Seconds and trying again.".format(api_name), exc_info=True)
                sleep(10)
                try:
                    apigw.delete_rest_api(
                        restApiId=api_id
                    )
                    logger.info("Deleted {}".format(api_name))
                    logger.info("Sleeping for 30 seconds")        
                    sleep(30)
                except (SystemExit, KeyboardInterrupt):
                    raise
                except:
                    logger.warn('Failed to delete {}'.format(api_name), exc_info=True)
                    sleep(10)
                    pass            
            try:
                delete_api_log_group(api_name, log_groups)
            except Exception as e:
                logger.info("couldn't delete the log group", exc_info=True)

def delete_api_log_group(api_name, log_groups):
    if api_name in log_groups:
        for log_group in log_groups[api_name]:
            try:
                response = cwl.delete_log_group(
                    logGroupName=log_group
                )
                logger.info("Log Group {} has been removed".format(log_group))
            except cwl.exceptions.ResourceNotFoundException:
                logger.warn("Log Group {} has already been removed or it does not exist".format(log_group))


def delete_base_path_mappings(api_id, base_path_mappings):
    for domain_name, mappings in base_path_mappings.items():
        for mapping in mappings:
            if mapping[1] == api_id:
                base_path = mapping[0]
                try:
                    response = apigw.delete_base_path_mapping(
                        domainName=domain_name,
                        basePath=base_path
                    )
                    logger.info("Deleted base path {}".format(base_path))
                except apigw.exceptions.NotFoundException:
                    logger.warn("could not find base path mapping, may be unable to remove API", exc_info=True)
                    pass

def main():

    delete_these = []
    try:
        input_file = sys.argv[1]
        with open(input_file, 'r') as i:
            for line in i:
                delete_these.append(line.replace("\n", ""))
        logger.info("APIs to delete: {}".format(delete_these))
    except IndexError:
        logger.error("Missing input File", exc_info=True)

    base_path_mappings = get_basepaths()
   
    list_of_apis = get_apis()
    log_groups = get_log_groups(list_of_apis, delete_these)

    delete_apis(list_of_apis, delete_these, log_groups, base_path_mappings)

if __name__ == '__main__':
    main()
