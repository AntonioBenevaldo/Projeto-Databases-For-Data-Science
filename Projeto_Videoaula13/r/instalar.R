args <- commandArgs(trailingOnly = TRUE)
backend <- if (length(args) > 0 && args[[1]] == "postgres") "RPostgres" else "RSQLite"
# Biblioteca pessoal: dispensa gravar pacotes em Program Files.
lib <- Sys.getenv("R_LIBS_USER")
lib <- strsplit(lib, .Platform$path.sep, fixed = TRUE)[[1]][1]
if (!nzchar(lib)) stop("R_LIBS_USER nao definido. Confira a instalacao do R.")
dir.create(lib, recursive = TRUE, showWarnings = FALSE)
.libPaths(c(lib, .libPaths()))
for (p in c("DBI", backend)) {
  if (!requireNamespace(p, quietly = TRUE))
    install.packages(p, lib = lib, repos = "https://cloud.r-project.org")
  if (!requireNamespace(p, quietly = TRUE)) stop(paste("Falha ao instalar", p))
  cat(p, as.character(packageVersion(p)), "disponivel\n")
}
