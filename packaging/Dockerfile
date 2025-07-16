ARG BASE_IMAGE=sogno/dpsim:dev

FROM ${BASE_IMAGE} as builder

USER root

RUN pip uninstall dpsim

RUN cd /tmp && \
    git clone --recurse-submodules https://github.com/gnakti/dpsim.git && \
    cd /tmp/dpsim && \
	git checkout cretevalley-devs && \
	python3 -m build --sdist --outdir dist/ &&\
	python3 -m build --wheel && \
	mkdir /temp/ && \
	cp dist/*.whl /temp/


FROM ${BASE_IMAGE}

USER root
ENV DPS_ROOT=/dpsroot
ENV DPS_EXPORT=true
ENV DPS_MODE=local
ENV DPS_LOG_LEVEL=INFO

# Copy dpsim wheel package from base container & install the packages
COPY --from=builder /temp/*.whl /tmp/
RUN	pip install /tmp/*.whl

RUN pip install pandapower numba junix cimpy pandas openpyxl uvicorn fastapi python-multipart
RUN mkdir /dps
COPY src /dps
RUN mkdir /dpsroot
WORKDIR /dps
CMD ["uvicorn","api-script:app","--host" ,"0.0.0.0", "--port","5000"]