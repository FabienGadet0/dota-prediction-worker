FROM julia:1.5.2-buster

COPY . /app/app
WORKDIR /app/app

ENV PYTHON=
# RUN julia -e "using Pkg; ; pkg\"activate . \"; Pkg.add(\"PyCall\") ; Pkg.build(\"PyCall\")"
RUN julia -e "using Pkg; pkg\"activate . \"; pkg\"instantiate\";"
RUN julia -e "using Pkg; pkg\"activate . \"; using Conda; Conda.add(\"pandas\", Conda.ROOTENV); Conda.add(\"numpy\", Conda.ROOTENV); Conda.add(\"requests\", Conda.ROOTENV); Conda.add(\"termcolor\", Conda.ROOTENV);"

EXPOSE 8000:8000

ENTRYPOINT ["julia", "--project", "src/app.jl" , "--run-as-a-server"]