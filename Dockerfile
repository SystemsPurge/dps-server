FROM soullessblob/cv-dpsim-builder:alpha AS builder
USER root
ENV DPS_ROOT=/dpsroot
ENV DPS_MODE=local
ENV DPS_LOG_LEVEL=INFO

RUN pip install pandapower numba junix cimpy pandas openpyxl uvicorn fastapi python-multipart
RUN mkdir /dps
COPY src /dps
RUN mkdir /dpsroot
WORKDIR /dps
RUN echo -e "#!/bin/bash\nexec python /dps/cli-script.py \"\$@\"" > /usr/local/bin/dps \
&& chmod +x /usr/local/bin/dps
CMD ["uvicorn","api-script:app","--host" ,"0.0.0.0", "--port","5000"]