install.packages("plyr")
install.packages("dplyr")


library(plyr)
library(dplyr)


sessions <- read.csv("~/abb/ts_abb.csv", stringsAsFactors = FALSE)

#duration of the sessions
sessions$start <- as.POSIXct(sessions$start)
sessions$end <- as.POSIXct(sessions$end)
sessions$duration <- difftime(sessions$end, sessions$start, units = "min")
quantile(sessions$duration/60) #median 7.5 hours
mean(sessions$duration/60) #9.16 hours

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


