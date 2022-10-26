import yaml
import os

from dotenv import load_dotenv
load_dotenv()

run_prometheus = True
run_loki = True
run_provisoning_datasources = True
run_contactpoint = True
run_client_promtail = True
run_client_bcexporter = True
run_docker_compose = True
run_client_docker_compose = True

template_prometheus = './templates/prometheus.yml'
output_prometheus = './prometheus/prometheus.yml'

template_loki = './templates/loki-config.yml'
output_loki = './loki/loki-config.yml'

template_datasource = './templates/datasources'
output_datasource = './grafana_provisioning/datasources'

template_contactpoint = './templates/alerting/contactpoint.yaml'
output_contactpoint = './grafana_provisioning/alerting/contactpoint.yaml'

template_client_promtail = './templates/clients/promtail-config.yml'
output_client_promtail = './clients/promtail/promtail-config.yml'

template_client_bcexporter = './templates/clients/config.yml'
output_client_bcexporter = './clients/bcexporter/config/config.yml'

template_docker_compose = './templates/docker-compose.yml'
output_docker_compose = './docker-compose.yml'

template_client_docker_compose = './templates/clients/docker-compose.yml'
output_client_docker_compose = './clients/docker-compose.yml'

if run_prometheus:
    with open(template_prometheus, "r") as f:
        newdict = yaml.safe_load(f)
    list_scrape_configs = newdict["scrape_configs"]
    for idx, scrape_config in enumerate(list_scrape_configs):
        job_name = scrape_config["job_name"]
        if job_name == 'node':
            scrape_config["static_configs"][0]["targets"] = [os.getenv("LOGGING_ENDPOINT") + ':' + os.getenv("NODE_EXPORTER_PORT")]
        elif job_name == 'blockchain':
            scrape_config["static_configs"][0]["targets"] = [os.getenv("LOGGING_ENDPOINT") + ':' + os.getenv("BLOCKCHAIN_EXPORTER_PORT")]
        elif job_name == 'cadvisor':
            scrape_config["static_configs"][0]["targets"] = [os.getenv("LOGGING_ENDPOINT") + ':' + os.getenv("CADVISOR_EXPORTER_PORT")]
        else:
            print(f'Unknown prometheus job name {job_name}')
        list_scrape_configs[idx] = scrape_config
    newdict["scrape_configs"] = list_scrape_configs
    with open(output_prometheus, "w") as f:
        yaml.dump(newdict, f)

if run_loki:
    with open(template_loki, "r") as f:
        newdict = yaml.safe_load(f)
    newdict["server"]["http_listen_port"] = int(os.getenv("LOKI_PORT"))
    with open(output_loki, "w") as f:
        yaml.dump(newdict, f)

if run_provisoning_datasources:
    for source in ['loki', 'prometheus']:
        with open(f'{template_datasource}/{source}.yaml', "r") as f:
            newdict = yaml.safe_load(f)
        newdict["datasources"][0]["url"] = 'https://' + os.getenv("MONITORING_ENDPOINT") + ':' + os.getenv(f'{source.upper()}_PORT')
        with open(f'{output_datasource}/{source}.yaml', "w") as f:
            yaml.dump(newdict, f)

if run_contactpoint:
    with open(template_contactpoint, "r") as f:
        newdict = yaml.safe_load(f)
    newdict["contactPoints"][0]["receivers"][0]["settings"]["url"] = os.getenv("SLACK_WEBHOOK")
    with open(output_contactpoint, "w") as f:
        yaml.dump(newdict, f)

if run_client_promtail:
    with open(template_client_promtail, "r") as f:
        newdict = yaml.safe_load(f)
    newdict["clients"][0]["url"] = 'https://' + os.getenv('MONITORING_ENDPOINT') + ':' + os.getenv('LOKI_PORT') + '/loki/api/v1/push'
    newdict["server"]["http_listen_port"] = int(os.getenv('PROMTAIL_PORT'))
    with open(output_client_promtail, "w") as f:
        yaml.dump(newdict, f)

if run_client_bcexporter:
    with open(template_client_bcexporter, "r") as f:
        newdict = yaml.safe_load(f)
    newdict["exporter_port"] = int(os.getenv('BLOCKCHAIN_EXPORTER_PORT'))
    with open(output_client_bcexporter, "w") as f:
        yaml.dump(newdict, f)

if run_docker_compose:
    with open(template_docker_compose, "r") as f:
        newdict = yaml.safe_load(f)
    list_services = newdict["services"]
    for (k, v) in list_services.items():
        if k not in ('loki', 'grafana', 'minio', 'prometheus', 'alertmanager'):
            print(f'Unknown service {k} in docker-compose')
            continue
        list_services[f'{k}']['ports'] = [os.getenv(f'{k.upper()}_PORT') + ':' + os.getenv(f'{k.upper()}_PORT')]
    with open(output_docker_compose, "w") as f:
        yaml.dump(newdict, f)

if run_client_docker_compose:
    with open(template_client_docker_compose, "r") as f:
        newdict = yaml.safe_load(f)
    list_services = newdict["services"]
    for (k, v) in list_services.items():
        if k not in ('blockchain_exporter', 'promtail', 'node_exporter', 'cadvisor'):
            print(f'Unknown service {k} in clients/docker-compose')
            continue
        list_services[f'{k}']['ports'] = [os.getenv(f'{k.upper()}_PORT') + ':' + os.getenv(f'{k.upper()}_PORT')]
    with open(output_client_docker_compose, "w") as f:
        yaml.dump(newdict, f)
