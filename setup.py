from pathlib import Path
import yaml
import os
import argparse


'''
This method parses several environment variables and returns the values in a dictionary.
'''


def _get_env_vars():
    env_vars = [
        "NODE_EXPORTER_ENDPOINT", "NODE_EXPORTER_PORT", "BLOCKCHAIN_EXPORTER_ENDPOINT",
        "BLOCKCHAIN_EXPORTER_PORT", "CADVISOR_EXPORTER_ENDPOINT", "CADVISOR_EXPORTER_PORT",
        "LOKI_PORT", "LOKI_ENDPOINT", "PROMETHEUS_ENDPOINT", "PROMETHEUS_PORT", "GRAFANA_PORT",
        "MINIO_PORT", "ALERTMANAGER_PORT", "PROMTAIL_PORT", "SLACK_WEBHOOK"
    ]
    env_var_dict = {}
    for env_var in env_vars:
        env_var_dict[env_var] = os.getenv(env_var)
    return env_var_dict


env_vars = _get_env_vars()


def get_template(template_path):
    with open(template_path, 'r') as f:
        template_dict = yaml.safe_load(f)
    return template_dict


def generate_config(completed_template, output_path):
    with open(output_path, "w") as f:
        yaml.dump(completed_template, f)


def update_prometheus_config():
    template_dict = get_template(('./templates/prometheus.yml'))
    for job_dict in template_dict["scrape_configs"]:
        targets_dict_path = ("static_configs", 0, "targets")
        if job_dict["job_name"] == "node":
            target = f"{env_vars['NODE_EXPORTER_ENDPOINT']}:{env_vars['NODE_EXPORTER_PORT']}"
            job_dict[targets_dict_path] = target
        elif job_dict["job_name"] == "blockchain":
            target = f"{env_vars['BLOCKCHAIN_EXPORTER_ENDPOINT']}:{env_vars['BLOCKCHAIN_EXPORTER_PORT']}"
            job_dict[targets_dict_path] = target
        elif job_dict["job_name"] == "cadvisor":
            target = f"{env_vars['CADVISOR_EXPORTER_ENDPOINT']}:{env_vars['CADVISOR_EXPORTER_PORT']}"
            job_dict[targets_dict_path] = target
        else:
            print(f"Unexpected prometheus job found in config: {job_name}")
    generate_config(template_dict, Path('./prometheus/prometheus.yml'))


def update_loki():
    template_dict = get_template(Path('./templates/loki-config.yml'))
    template_dict["server"]["http_listen_port"] = env_vars["LOKI_PORT"]
    generate_config(template_dict, Path('./loki/loki-config.yml'))


def update_datasource(datasource):
    if datasource.upper() != "LOKI" and datasource.upper() != "PROMETHEUS":
        print("invalid params passed for update_datasource")
    else:
        template_dict = get_template(
            Path(f'./templates/datasources/{datasource}.yaml'))
        endpoint = env_vars[f"{datasource.upper()}_ENDPOINT"]
        port = env_vars[f"{datasource.upper()}_PORT"]
        template_dict["datasources"][0]["url"] = f"{endpoint}:{port}"
        generate_config(template_dict, Path(
            f"./grafana_provisioning/datasources/{datasource}.yaml"))


def update_alerting_contactpoint():
    template_dict = get_template(
        Path('./templates/alerting/contactpoint.yaml'))
    template_dict["contactPoints"][0]["receivers"][0]["settings"]["url"] = env_vars["SLACK_WEBHOOK"]
    generate_config(template_dict, Path(
        './grafana_provisioning/alerting/contactpoint.yaml'))


def update_promtail():
    template_dict = get_template(
        Path("./templates/clients/promtail-config.yml"))
    template_dict["clients"][0]["url"] = f"{env_vars['LOKI_ENDPOINT']}:{env_vars['LOKI_PORT']}/loki/api/v1/push"
    template_dict["server"]["http_listen_port"] = env_vars["PROMTAIL_PORT"]
    generate_config(template_dict, Path(
        './clients/promtail/promtail-config.yml'))


def update_bcexporter():
    template_dict = get_template(Path('./templates/clients/config.yml'))
    template_dict["exporter_port"] = env_vars['BLOCKCHAIN_EXPORTER_PORT']
    generate_config(template_dict, Path(
        './clients/bcexporter/config/config.yml'))


def update_root_docker_compose():
    template_dict = get_template(Path('./templates/docker-compose.yml'))
    services = ["loki", "minio", "grafana", "prometheus"]
    for service in services:
        port_str = env_vars[f"{service.upper()}_PORT"]
        template_dict["services"][service]['ports'] = f"{port_str}:{port_str}"
    generate_config(template_dict, Path("./docker-compose.yml"))


def main():
    update_prometheus_config()
    update_loki()
    update_datasource("loki")
    update_datasource("prometheus")
    update_alerting_contactpoint()
    update_promtail()
    update_bcexporter()
    update_root_docker_compose()


if __name__ == "__main__":
    main()
