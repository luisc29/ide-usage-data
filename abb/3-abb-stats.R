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
quantile(sessions$n_inte)
mean(sessions$n_inte)

#duration of interruptions
inte.v <- lapply(strsplit(sessions$interruption," "),as.integer)
sessions$inte.v <- inte.v
inte.all <- unlist(inte.v)
quantile(inte.all[inte.all>0])
#median length of interruptions = 5

edit.v <- lapply(strsplit(sessions$edition," "),as.integer)
sessions$edit.v <- edit.v
nav.v <- lapply(strsplit(sessions$text_nav," "),as.integer)
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

#how many productive segments are there among all the sessions? (at least 30 minutes without interruptions)
productive.segments <- unlist(lapply(sessions$inte.v, function(x){
  res <- 0
  nx <- length(x)
  count <- 0
  flag <- FALSE
  for(i in c(1:nx)){
    if(x[[i]] > 0){
      count <- 0      
      if(flag){
        res <- res+1
        flag <- FALSE
      }
    }else{
      count <- count+1
      if(count >= 30 && !flag)
        flag <- TRUE
    }
  }
  res
}))
sum(productive.segments)

#count the number of events per type
sessions$n_edition <- unlist(lapply(sessions$edition, function(x) { 
  v <- as.numeric(unlist(strsplit(x," ")))
  sum(v)
}))

sessions$n_high_nav <- unlist(lapply(sessions$high_nav, function(x) { 
  v <- as.numeric(unlist(strsplit(x," ")))
  sum(v)
}))

sessions$n_text_nav <- unlist(lapply(sessions$text_nav, function(x) { 
  v <- as.numeric(unlist(strsplit(x," ")))
  sum(v)
}))

focus.v <- lapply(strsplit(sessions$focus," "),as.double)
sessions$focus.v <- focus.v
focus.v.len <- unlist(lapply(sessions$focus.v, function(x){
  length(x)
}))
inte.v.len <- unlist(lapply(sessions$inte.v, function(x){
  length(x)
}))

sessions$focus.size = focus.v.len
sessions$inte.size = inte.v.len
diff.focus.inte <- focus.v.len == inte.v.len
length(diff.focus.inte[diff.focus.inte == TRUE])

diff.focus.inte <- (sessions$focus.size/sessions$inte.size)*100
