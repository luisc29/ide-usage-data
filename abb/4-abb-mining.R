install.packages("plyr")
install.packages("dplyr")
install.packages("ggplot2")
install.packages("gridExtra")
install.packages("ggthemes")

library(plyr)
library(dplyr)
library(ggplot2)
library(ggthemes)
library(grid)
library(gridExtra)

sessions <- read.csv("~/abb/ts_abb2.csv", stringsAsFactors = FALSE)
users <- read.csv("~/abb/export-2015-10-23/tinyusers.csv", stringsAsFactors=FALSE)
focus <- read.csv("~/abb/focus.clean.csv", stringsAsFactors=FALSE)


# number of sessions
nrow(sessions)

# number of users
length(unique(sessions$user))

# number of events per session
mean(sessions$n_events)
quantile(sessions$n_events)

# amount of sessions per user
res <- summary(as.factor(sessions$user))
mean(res)
quantile(res)

# what's the duration of sessions?
sessions$start <- as.POSIXct(sessions$start)
sessions$end <- as.POSIXct(sessions$end)
sessions$duration <- difftime(sessions$end, sessions$start, units = "hours")
quantile(sessions$duration) #median 7.5 hours
mean(sessions$duration) #9.16 hours
sd(sessions$duration)
ggplot(sessions[sessions$size_ts < (200),], aes(x=duration)) + geom_histogram() + 
  labs(x="Sessions' duration (hours)", y="Count")+ theme_hc() 

# what's the distribution of productive time?
quantile(sessions$size_ts)

# statistics of the number of interruptions per session
quantile(sessions$n_inte)
mean(sessions$n_inte)

# duration of interruptions
inte.v <- lapply(strsplit(sessions$interruptions," "),as.integer)
sessions$inte.v <- inte.v
inte.all <- unlist(inte.v)
quantile(inte.all[inte.all>0]) 

# edit.v <- lapply(strsplit(sessions$edition," "),as.integer)
# sessions$edit.v <- edit.v
# nav.v <- lapply(strsplit(sessions$text_nav," "),as.integer)
# sessions$nav.v <- nav.v

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

Sys.setlocale("LC_TIME", "C")

# productive hours according to focus
focus$datetime <- as.POSIXlt(focus$datetime)
focus$hour <- focus$datetime$hour
focus.agg <- aggregate(focus$focus, list(focus$hour), sum)
names(focus.agg) <- c("hour", "focus")
focus.agg$focus <- focus.agg$focus/max(focus.agg$focus)
ggplot(focus.agg, aes(x=hour, y=focus)) + geom_bar(stat="identity") + scale_x_continuous(breaks = 0:23) + 
  labs(x = "Hour of the day", y = "Focus (normalized)") + theme_few() 

# productive days according to focus
focus$day <- weekdays(focus$datetime)
focus.agg <- aggregate(focus$focus, list(focus$day), sum)
names(focus.agg) <- c("day", "focus")
focus.agg$day <- factor(focus.agg$day, levels= c("Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"))
focus.agg$focus <- focus.agg$focus/max(focus.agg$focus)
ggplot(focus.agg, aes(x=day, y=focus)) + geom_bar(stat="identity") + labs(x = "Day of the week", y = "Focus (normalized)") + theme_few() 

# users and focus
# focus.agg <- aggregate(focus$focus, list(focus$user), mean)
# names(focus.agg) <- c("user","focus")
# focus.agg$origin <- unlist(lapply(focus.agg$user, function(x){
#   email <- users[users$Username == x, "PrimaryEmail"]
#   if(length(email) > 0){
#     strsplit(email, ".", fixed=TRUE)[[1]][1] 
#   }else{
#     ""
#   }
# }))
# focus.agg <- focus.agg[focus.agg$origin != "",]
# focus.agg$n_inte <- unlist(lapply(focus.agg$user, function(x){
#   sum(sessions[sessions$user == x,]$n_inte)
# }))
# focus.agg <- focus.agg[focus.agg$n_inte > 0 & (focus.agg$origin == "us" | focus.agg$origin == "in"),]
# ggplot(focus.agg, aes(x=n_inte, y=focus, color=origin)) + geom_point() + theme_few() 

# focus.agg <- aggregate(focus.agg$focus, list(focus.agg$origin), sum)
# names(focus.agg) <- c("origin", "focus")
# users$origin <- unlist(lapply(users$PrimaryEmail, function(x){
#   strsplit(x, ".", fixed=TRUE)[[1]][1]
# }))
# users <- users[!is.na(users$origin),]
# users.agg <- aggregate(users$origin, list(users$origin), length)  
# names(users.agg) <- c("origin", "count")



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
inte.exp.v <- lapply(strsplit(sessions$interruptions_expanded," "),as.double)
sessions$focus.v <- focus.v
sessions$inte.exp.v <- inte.exp.v
focus.v.len <- unlist(lapply(sessions$focus.v, function(x){
  length(x)
}))
inte.exp.v.len <- unlist(lapply(sessions$inte.exp.v, function(x){
  length(x)
}))
inte.v.len <- unlist(lapply(sessions$inte.v, function(x){
  length(x)
}))

sessions$focus.size = focus.v.len
sessions$inte.size = inte.v.len
sessions$inte.exp.size = inte.exp.v.len

diff.focus.inte <- focus.v.len == inte.v.len
length(diff.focus.inte[diff.focus.inte == TRUE])

diff.focus.inte <- (sessions$focus.size/sessions$inte.size)*100

