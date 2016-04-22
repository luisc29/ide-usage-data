install.packages("plyr")
install.packages("dplyr")


library(plyr)
library(dplyr)

sessions <- read.csv("~/abb/ts_abb.csv", stringsAsFactors = FALSE)

#duration of the sessions
sessions$start <- as.POSIXct(sessions$start)
sessions$end <- as.POSIXct(sessions$end)
sessions$duration <- difftime(sessions$end, sessions$start, units = "min")
quantile(sessions$duration) #median 7.5 hours
mean(sessions$duration)/60 #9.16 hours

#productive time
quantile(sessions$size_ts)

#number of interruptions per session
quantile(sessions$num_inte)
mean(sessions$num_inte)

#duration of interruptions
inte.v <- lapply(strsplit(sessions$interruption," "),as.integer)
sessions$inte.v <- inte.v
inte.all <- unlist(inte.v)
quantile(inte.all[inte.all>0])
#median length of interruptions = 5

edit.v <- lapply(strsplit(sessions$edits," "),as.integer)
sessions$edit.v <- edit.v
nav.v <- lapply(strsplit(sessions$navigation," "),as.integer)
sessions$nav.v <- nav.v

#when does the big interruptions occur?
sessions.old <- read.csv("~/abb/ts_abb (copy).csv", stringsAsFactors=FALSE)
inte.v <- lapply(strsplit(sessions.old$interruption," "),as.integer)
when <- unlist(lapply(inte.v, function(x){
  inte.big.threshold <- 45
  res <- c()
  l <- length(x)
  for(i in c(1:l)){
    if(x[i] >= inte.big.threshold){
      res <- c(res,(i/l))
    }
  }
  res
}))

mean(when)
quantile(when)
hist(when)
