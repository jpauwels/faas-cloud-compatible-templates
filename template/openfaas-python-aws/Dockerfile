ARG PYTHON_VERSION=3.12
ARG PYTHON_OS=alpine
FROM ghcr.io/openfaas/of-watchdog:0.9.10 AS watchdog
FROM python:${PYTHON_VERSION}-${PYTHON_OS} AS build

COPY --from=watchdog --chmod=755 /fwatchdog /usr/bin/fwatchdog

ARG UPGRADE_PACKAGES=Y
ARG ADDITIONAL_PACKAGE=''
RUN if [ -n "$(which apk)" ]; then \
        if [ "${UPGRADE_PACKAGES}" = "Y" ]; then apk --no-cache upgrade; fi \
        && apk --no-cache add ${ADDITIONAL_PACKAGE}; \
    else \
        apt-get update -qy \
        && if [ "${UPGRADE_PACKAGES}" = "Y" ]; then apt-get upgrade -qy; fi \
        && apt-get install -qy --no-install-recommends ${ADDITIONAL_PACKAGE} \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Add non root user
RUN addgroup --system app && adduser app --system --ingroup app --home /home/app && chown app:app /home/app
USER app
ENV PATH=$PATH:/home/app/.local/bin

# Install template requirements
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt pip install --no-cache-dir --user -r requirements.txt

# Install user-specified requirements
RUN --mount=type=bind,source=function/requirements.txt,target=requirements.txt pip install --no-cache-dir --user -r requirements.txt

# Copy template and function code
WORKDIR /home/app/
COPY --chown=app:app index.py .
RUN mkdir -p function
COPY --chown=app:app function function


FROM build AS test
ARG TEST_COMMAND=tox
ARG TEST_ENABLED=true
RUN [ "$TEST_ENABLED" = "false" ] && echo "skipping tests" || eval "$TEST_COMMAND"


FROM build AS ship

# Configure WSGI server and healthcheck
ENV fprocess="python index.py"
ENV cgi_headers="true"
ENV mode="http"
ENV upstream_url="http://127.0.0.1:5000"

HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]
EXPOSE 8080
