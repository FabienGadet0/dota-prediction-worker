
using Pkg

metadata_packages = [
    "CSV",
    "DataFrames",
    "DotEnv",
    "IterTools",
    # "HTTP",
    "LibPQ",
    "Missings",
    "DataFramesMeta",
    "ArgParse",
    "Match",
    "Conda",
    "Query",
    "Tables",
    "PyCall",
    "MLJ",
    "MLJScikitLearnInterface"
]

Pkg.update()

for package = metadata_packages
    Pkg.add(package)
end
Pkg.add("PyCall")
Pkg.add("Conda")

Pkg.build("PyCall")
Pkg.instantiate()

import Conda




Conda.add("pandas", Conda.ROOTENV)
Conda.add("numpy", Conda.ROOTENV)
Conda.add("requests", Conda.ROOTENV)
Conda.add("termcolor", Conda.ROOTENV)


# Pkg.build("PyCall")

using DotEnv, ArgParse,  Match, DataFrames, CSV , Query, LibPQ, DataFramesMeta, PyCall


# need to build XGBoost version for it to work
# Pkg.clone("https://github.com/antinucleon/XGBoost.jl.git")
# Pkg.build("XGBoost")

# Pkg.clone("https://github.com/benhamner/MachineLearning.jl")
# Pkg.pin("MachineLearning")

# Pkg.clone("https://github.com/Allardvm/LightGBM.jl.git")
# ENV["LIGHTGBM_PATH"] = "../LightGBM"