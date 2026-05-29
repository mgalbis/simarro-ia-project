FROM golang:1.25-alpine AS builder

ARG LAKEFS_VERSION=v1.81.1

RUN apk add --no-cache git
RUN git clone --depth 1 --branch ${LAKEFS_VERSION} https://github.com/treeverse/lakeFS.git /src/lakefs
WORKDIR /src/lakefs
RUN go build -o /out/acl ./contrib/auth/acl/cmd/acl

FROM alpine:3.21

RUN apk add --no-cache ca-certificates tzdata

COPY --from=builder /out/acl /usr/local/bin/acl

ENTRYPOINT ["acl", "run"]
