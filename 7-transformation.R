library(plyr)
library(dplyr)
library(tidyr)
library(ggplot2)

# load the data
udc.chunks <- read.csv("~/udc/udc.chunks.csv", stringsAsFactors = FALSE)
udc.chunkcenters <- read.csv("~/udc/udc.chunkscenters.csv", stringsAsFactors=FALSE)
udc.sessions <- read.csv("~/udc/udc.sessions.csv", stringsAsFactors = FALSE)
udc.sessionssplit <- read.csv("~/udc/udc.splittedsessions.csv", stringsAsFactors=FALSE)

abb.chunks <- read.csv("~/abb/abb.chunks.csv", stringsAsFactors = FALSE)
abb.chunkcenters <- read.csv("~/abb/abb.chunkscenters.csv", stringsAsFactors=FALSE)
abb.sessions <- read.csv("~/abb/abb.sessions.csv", stringsAsFactors = FALSE)
abb.sessionssplit <- read.csv("~/abb/abb.splittedsessions.csv", stringsAsFactors=FALSE)

sessions.transform <- function(sessions, sessions.labels){
  # remove useless sessions
  sessions <- sessions[sessions$label != -1,]
  sessions[sessions$label == sessions.labels[1], ]$label <- "Type A"
  sessions[sessions$label == sessions.labels[2], ]$label <- "Type B"
  sessions[sessions$label == sessions.labels[3], ]$label <- "Type C"
  sessions[sessions$label == sessions.labels[4], ]$label <- "Type D"
  sessions[sessions$label == sessions.labels[5], ]$label <- "Type E"
  sessions
}

sessionssplit.transform <- function(sessionssplit){
  # transform the data into a long form, decreasing the columns and
  # increasing the rows
  sessionssplit <- gather(sessionssplit,id,label)
  # rename the columns
  names(sessionssplit) <- c("id", "label", "activity","value")
  # split activity column into activity and phase
  sessionssplit <- separate(sessionssplit, activity, c("activity","phase"))
  
  sessionssplit
}

sessionssplit.filter.and.agg <- function(sessionssplit, chosen.session.labels, chunks.labels){
  # filter the sessions according to the selected labels
  sessionssplit <- sessionssplit[sessionssplit$label %in% chosen.session.labels,]
  
  # aggregate the sessions.split dataset and plot the data
  sessionssplit$id <- NULL
  sessionssplit.agg <- aggregate(sessionssplit, by=list(sessionssplit$label, sessionssplit$activity,
                                                        sessionssplit$phase), FUN=mean)
  # rename columns
  sessionssplit.agg$label <- NULL
  sessionssplit.agg$activity <- NULL
  sessionssplit.agg$phase <- NULL
  names(sessionssplit.agg) <- c("label", "activity", "phase", "value")
  sessionssplit.agg$value <- sessionssplit.agg$value*100
  
  sessionssplit.agg[sessionssplit.agg$label == chosen.session.labels[1], ]$label <- "Type A"
  sessionssplit.agg[sessionssplit.agg$label == chosen.session.labels[2], ]$label <- "Type B"
  sessionssplit.agg[sessionssplit.agg$label == chosen.session.labels[3], ]$label <- "Type C"
  sessionssplit.agg[sessionssplit.agg$label == chosen.session.labels[4], ]$label <- "Type D"
  sessionssplit.agg[sessionssplit.agg$label == chosen.session.labels[5], ]$label <- "Type E"
  
  sessionssplit.agg$label <- factor(sessionssplit.agg$label, levels = c("Type A", "Type B", "Type C", "Type D", "Type E"))
  sessionssplit.agg$activity <- factor(sessionssplit.agg$activity, levels = chunks.labels)
  sessionssplit.agg$phase <- as.numeric(sessionssplit.agg$phase)
  sessionssplit.agg$value.log <- log(sessionssplit.agg$value)
  sessionssplit.agg
}

chunks.transform <- function(chunks, chunkcenters){
  # add the label to every chunk
  chunks$label.c <- unlist(lapply(chunks$label, function(x){
    chunkcenters[x+1,]$label[1]
  }))
  chunks
}

pipeline <- function(chunks, chunkscenters, sessions, sessionssplit, sessions.labels, chunks.labels,
                     directory, data.name){
  sessions <- sessions.transform(sessions, sessions.labels)
  sessionssplit <- sessionssplit.transform(sessionssplit)
  sessionssplit <- sessionssplit.filter.and.agg(sessionssplit, session.labels, chunks.labels)
  chunks <- chunks.transform(chunks, chunkscenters)
  
  write.csv(sessions, paste(directory,data.name,".","sessions2.csv", sep=""), row.names = FALSE)
  write.csv(sessionssplit, paste(directory,data.name,".","splittedsessions2.csv", sep=""), row.names=FALSE)
  print(paste(directory,data.name,".","chunks.csv", sep=""))
  write.csv(chunks, paste(directory,data.name,".","chunks.csv", sep=""), row.names=FALSE)
}

#UDC
sorted.sessions.type <- sort(summary(as.factor(udc.sessions$label)), decreasing=TRUE)
sorted.sessions.type[0:10]
session.labels <- c(21, 38, 86, 79, 83)
chunk.labels <- c("Programming", "Debugging", "Version", "Navigation")
pipeline(udc.chunks, udc.chunkcenters, udc.sessions, udc.sessionssplit, session.labels, chunk.labels,
         "~/udc/", "udc")

#ABB
sorted.sessions.type <- sort(summary(as.factor(abb.sessions$label)), decreasing=TRUE)
sorted.sessions.type[0:10]
session.labels <- c(31, 16, 5, 20, 0)
chunk.labels <- c("Programming", "Debugging", "Version", "Navigation")
pipeline(abb.chunks, abb.chunkcenters, abb.sessions, abb.sessionssplit, session.labels, chunk.labels,
         "~/abb/", "abb")
