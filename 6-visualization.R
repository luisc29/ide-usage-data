library(plyr)
library(dplyr)
library(tidyr)
library(ggplot2)
library(ggthemes)
library(grid)
library(gridExtra)

# load the data
udc.chunks <- read.csv("~/udc/chunks_udc.csv", stringsAsFactors = FALSE)
udc.chunkcenters <- read.csv("~/udc/chunks_centers_udc.csv", stringsAsFactors=FALSE)
udc.sessions <- read.csv("~/udc/ts_udc.csv", stringsAsFactors = FALSE)
udc.sessionscenters <- read.csv("~/udc/sessions_centers_udc.csv", stringsAsFactors=FALSE)
udc.sessionssplit <- read.csv("~/udc/splitted_sessions_udc.csv", stringsAsFactors=FALSE)

abb.chunks <- read.csv("~/abb/chunks_abb.csv", stringsAsFactors = FALSE)
abb.chunkcenters <- read.csv("~/abb/chunks_centers_abb.csv", stringsAsFactors=FALSE)
abb.sessions <- read.csv("~/abb/ts_abb.csv", stringsAsFactors = FALSE)
abb.sessionscenters <- read.csv("~/abb/sessions_centers_abb.csv", stringsAsFactors=FALSE)
abb.sessionssplit <- read.csv("~/abb/splitted_sessions_abb.csv", stringsAsFactors=FALSE)

sessions.transform <- function(sessions, sessions.labels){
  # remove useless sessions
  sessions <- sessions[sessions$label != -1,]
  sessions[sessions$label == sessions.labels[1], ]$label <- "Type A"
  sessions[sessions$label == sessions.labels[2], ]$label <- "Type B"
  sessions[sessions$label == sessions.labels[3], ]$label <- "Type C"
  sessions[sessions$label == sessions.labels[4], ]$label <- "Type D"
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

sessionssplit.filter.and.agg <- function(sessionssplit, chosen.session.labels, chosen.chunks){
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
  
  #sessionssplit.agg[sessionssplit.agg$phase == 1, ]$phase <- "Phase 1"
  #sessionssplit.agg[sessionssplit.agg$phase == 2, ]$phase <- "Phase 2"
  #sessionssplit.agg[sessionssplit.agg$phase == 3, ]$phase <- "Phase 3"
  
  sessionssplit.agg$label <- factor(sessionssplit.agg$label, levels = c("Type A", "Type B", "Type C", "Type D"))
  sessionssplit.agg$activity <- factor(sessionssplit.agg$activity, levels = chosen.chunks)
  sessionssplit.agg$phase <- as.numeric(sessionssplit.agg$phase)
  sessionssplit.agg$value.log <- log(sessionssplit.agg$value)
  sessionssplit.agg
}

chunks.transform <- function(chunks, chunkcenters){
  # add the label to every chunk
  chunks$label.c <- unlist(lapply(chunks$label, function(x){
    chunkcenters[chunkcenters$id == x,]$label[1]
  }))
  chunks
}

save.plot <- function(plot, name, w, h){
  png(paste(name,".png",sep=""), width = w, height = h, units="px")
  #png(paste(name,".png",sep=""))
  print(plot)
  dev.off()
}

plot.phases.by.session.type <- function(data, data.name, plot.name, width, height){
  plot <- ggplot(data, aes(x=phase, y=log(value), color=activity)) + 
          geom_point(size=4, alpha=0.7) + geom_line(aes(group=activity), size=1.2, alpha=0.7) + 
          labs(x="Phases", y="log(Average Proportion)", color="Activity", title=paste("Proportion of activities by session phase in",data.name)) +
          scale_x_continuous(breaks = 1:3) + scale_y_continuous(limits=c(-5,4)) +
          facet_grid(label ~ .) + theme_few() +  scale_colour_few() + theme(legend.position="bottom")
  save.plot(plot, plot.name, width, height)
}

pipeline <- function(chunks, chunkscenters, sessions, sessionscenters, sessionssplit, sessions.labels, 
                     chunks.labels, plot1.name, data.name){
  sessions <- sessions.transform(sessions, sessions.labels)
  sessionssplit <- sessionssplit.transform(sessionssplit)
  sessionssplit <- sessionssplit.filter.and.agg(sessionssplit, session.labels, chunks.labels)
  chunks <- chunks.transform(chunks, chunkscenters)
  
  cat("| Number of sessions:\t\t", nrow(sessions))
  cat("\n| Number of users:\t\t", length(unique(sessions$user)))
  cat("\n| Average session length:\t", mean(sessions$size_ts))
  cat("\n| Number of usable sessions:\t", nrow(sessions[sessions$label %in% c("Type A", "Type B", "Type C", "Type D"),]))
  cat("\n| Number of sessions by type:\n")
  s <- summary(as.factor(sessions[sessions$label %in% c("Type A", "Type B", "Type C", "Type D"),]$label))
  cat("|\t Type A:", s[1])
  cat("\n|\t Type B:", s[2])
  cat("\n|\t Type C:", s[3])
  cat("\n|\t Type D:", s[4])
  cat("\n| Number of chunks:\t\t", nrow(chunks))
  cat("\n| Number of chunks by type:")
  for(i in chunks.labels){
    cat("\n|\t", i, ": ", nrow(chunks[chunks$label.c == i,]))
  }
  cat("\n")
  plot.phases.by.session.type(sessionssplit, data.name, plot.name = plot1.name, width = 500, height = 800)
}

# ABB
# find the sessions types to work with
sorted.sessions.type <- sort(summary(as.factor(abb.sessions$label)), decreasing=TRUE)
sorted.sessions.type[0:5]
session.labels <- c(18, 26, 1, 20)
chunk.labels <- c("Programming", "Debugging", "Version", "Navigation", "Testing")
cat("Statistics ABB data")
pipeline(abb.chunks, abb.chunkcenters, abb.sessions, abb.sessionscenters, abb.sessionssplit, 
         session.labels, chunk.labels, "abb.phases", "ABB")


# UDC
# find the sessions types to work with
sorted.sessions.type <- sort(summary(as.factor(udc.sessions$label)), decreasing=TRUE)
sorted.sessions.type[0:5]
session.labels <- c(55, 70, 20, 17)
chunk.labels <- c("Programming", "Debugging", "Version", "Refactoring", "Tools")
cat("Statistics UDC data")
pipeline(udc.chunks, udc.chunkcenters, udc.sessions, udc.sessionscenters, udc.sessionssplit, 
         session.labels, chunk.labels, "udc.phases", "UDC")
