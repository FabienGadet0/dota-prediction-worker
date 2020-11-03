FROM julia:1.5.2-buster

COPY . /app
WORKDIR /app

ENV PYTHON=

# RUN julia -e "using Pkg; ; pkg\"activate . \"; Pkg.add(\"PyCall\") ; Pkg.build(\"PyCall\")"
RUN julia --project=. -e 'using Pkg; Pkg.add("ArgParse") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("CSV") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("Conda") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("DataFrames") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("DataFramesMeta") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("Dates") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("DotEnv") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("Genie") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("IterTools") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("JLSO") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("JSON") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("LibPQ") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("MLJ") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("MLJModels") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("MLJScikitLearnInterface") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("Match") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("PrettyPrinting") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("Query") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("PyCall") ;' 
RUN julia --project=. -e 'using Pkg; Pkg.add("Tables");'

# RUN julia -e "using Pkg;  pkg\"instantiate\"; pkg\"precompile\";"
RUN julia --project=. -e "using Conda; Conda.add(\"pandas\", Conda.ROOTENV); Conda.add(\"numpy\", Conda.ROOTENV); Conda.add(\"requests\", Conda.ROOTENV); Conda.add(\"termcolor\", Conda.ROOTENV);"
RUN julia --project=. -e "using Pkg;  pkg\"instantiate\" ; pkg\"build\" ; pkg\"precompile\";"

# EXPOSE 8000

ENTRYPOINT ["julia", "--project=.",  "src/app.jl", "--serve"]