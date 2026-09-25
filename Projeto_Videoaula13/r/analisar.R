# Executado por Python, mas a conexao e a analise abaixo sao realmente feitas em R.
main <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  if (length(args) != 6) stop("Use python projeto.py r")
  root <- args[[1]]; banco <- args[[2]]; inicio <- args[[3]]; fim <- args[[4]]
  lote <- as.integer(args[[5]]); saida <- args[[6]]
  if (!requireNamespace("DBI", quietly = TRUE)) stop("Execute python projeto.py r-instalar")
  if (banco == "sqlite") {
    db <- file.path(root, "data", "vendas.db")
    if (!file.exists(db)) stop("Execute python projeto.py preparar primeiro.")
    con <- DBI::dbConnect(RSQLite::SQLite(), dbname = db, flags = RSQLite::SQLITE_RO)
  } else {
    con <- DBI::dbConnect(RPostgres::Postgres(), host = Sys.getenv("PGHOST", "127.0.0.1"),
       port = as.integer(Sys.getenv("PGPORT", "5432")), dbname = Sys.getenv("PGDATABASE"),
       user = Sys.getenv("PGUSER"), password = Sys.getenv("PGPASSWORD"))
  }
  on.exit(DBI::dbDisconnect(con), add = TRUE)
  # dbGetQuery e conveniente quando o resultado e pequeno.
  cat("Conexao DBI ativa:", DBI::dbGetQuery(con, "SELECT 1 AS ok")$ok, "\n")
  sql <- paste(readLines(file.path(root,"sql","extracao.sql"), warn = FALSE, encoding="UTF-8"), collapse="\n")
  # Troca somente marcadores conhecidos; valores continuam separados no dbBind.
  for (i in seq_along(c(":status",":inicio",":fim"))) {
    marcador <- c(":status",":inicio",":fim")[[i]]
    sql <- gsub(marcador, if (banco == "postgres") paste0("$",i) else "?", sql, fixed=TRUE)
  }
  buscar <- function() {
    rs <- DBI::dbSendQuery(con, sql)
    on.exit(DBI::dbClearResult(rs), add=TRUE)
    DBI::dbBind(rs, list("concluida", inicio, fim))
    partes <- list()
    repeat {
      parte <- DBI::dbFetch(rs, n=lote)
      if (nrow(parte) == 0) break
      partes[[length(partes)+1]] <- parte
      cat("Lote R:",nrow(parte),"venda(s)\n")
    }
    if (length(partes)) do.call(rbind,partes) else DBI::dbFetch(rs,n=0)
  }
  df <- buscar()
  df$data_venda <- as.character(df$data_venda)
  if (anyNA(df) || anyDuplicated(df$venda_id)) stop("Dados ausentes ou duplicados")
  if (any(df$quantidade <= 0) || any(df$desconto_centavos < 0) ||
      any(df$desconto_centavos > df$quantidade*df$preco_centavos)) stop("Valores invalidos")
  dir.create(saida,recursive=TRUE,showWarnings=FALSE)
  write.csv(df,file.path(saida,"vendas_extraidas.csv"),row.names=FALSE,fileEncoding="UTF-8")
  df$faturamento_centavos <- df$quantidade*df$preco_centavos-df$desconto_centavos
  df$custo_total_centavos <- df$quantidade*df$custo_centavos
  df$lucro_bruto_centavos <- df$faturamento_centavos-df$custo_total_centavos
  df$mes <- substr(df$data_venda,1,7)
  metricas <- c("faturamento_centavos","custo_total_centavos","lucro_bruto_centavos")
  for (grupo in c("categoria","mes")) {
    if (nrow(df)) {
      resumo <- aggregate(df[metricas], by=setNames(list(df[[grupo]]),grupo), FUN=sum)
      resumo <- resumo[order(resumo[[grupo]]),]
    } else resumo <- df[FALSE,c(grupo,metricas)]
    arquivo <- if (grupo == "categoria") "resumo_categoria.csv" else "resumo_mensal.csv"
    write.csv(resumo,file.path(saida,arquivo),row.names=FALSE,fileEncoding="UTF-8")
    print(resumo)
  }
  fat <- sum(df$faturamento_centavos); custo <- sum(df$custo_total_centavos)
  indicadores <- data.frame(vendas=nrow(df),unidades=sum(df$quantidade),
    faturamento_centavos=fat,custo_total_centavos=custo,lucro_bruto_centavos=fat-custo,
    ticket_medio_reais=if(nrow(df)) round(fat/nrow(df)/100,2) else NA_real_,
    margem_bruta_percentual=if(fat>0) round((fat-custo)/fat*100,2) else NA_real_)
  write.csv(indicadores,file.path(saida,"indicadores.csv"),row.names=FALSE)
  print(indicadores)
  writeLines(c(paste("Extraido UTC:",format(Sys.time(),tz="UTC",usetz=TRUE)),
    paste("Banco:",banco),paste("Periodo:",inicio,fim),"Status: concluida",sql,
    capture.output(sessionInfo())),file.path(saida,"metadados_r.txt"))
  cat("R concluido. Execute python projeto.py comparar com as mesmas pastas de saida.\n")
}
tryCatch(main(),error=function(e) {
  message("Falha na etapa R. Confira pacotes, conexao, periodo e a etapa preparar. Tipo: ",class(e)[1])
  quit(status=1)
})
