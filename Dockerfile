FROM alpine
RUN nslookup dl-cdn.alpinelinux.org
RUN apk add -v curl
RUN curl -v http://www.google.com
RUN nslookup 8.8.8.8
