FROM soullessblob/cv-dpsim-builder:alpha AS builder
#prep env
ENV DPS_ROOT=/dpsroot
ENV DPS_MODE=local
ENV DPS_LOG_LEVEL=INFO
ENV DPS_DEFAULTS=/dps/defaults.json

#prep deps
ADD requirements.txt .
RUN pip install -r requirements.txt
RUN rm /requirements.txt

#prep fs
RUN mkdir /dps
COPY src /dps
COPY defaults.json /dps
RUN mkdir /dpsroot
WORKDIR /dps

#mimic cli
RUN echo -e "#!/bin/bash\nexec python /dps/cli-script.py \"\$@\"" > /usr/local/bin/dps \
&& chmod +x /usr/local/bin/dps

CMD ["uvicorn","api-script:app","--host" ,"0.0.0.0", "--port","5000"]