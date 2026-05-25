FROM treeverse/lakefs:latest

USER root

RUN apk add --no-cache jq curl

COPY docker/lakefs/entrypoint.sh /entrypoint.sh
COPY docker/lakefs/init_lakefs.sh /init_lakefs.sh
COPY docker/lakefs/hook-retrain.yml /init/hook-retrain.yml
COPY config/cases_config.json /init/cases_config.json

RUN chmod +x /entrypoint.sh /init_lakefs.sh

ENTRYPOINT ["/entrypoint.sh"]
