library(plyr)
library(dplyr)
library(tidyr)
library(ggplot2)
library(ggthemes)
library(grid)
library(gridExtra)
library(cluster)
library(clustertend)
library(factoextra)

# load the data
udc.chunks <- read.csv("~/udc/udc.chunks.csv", stringsAsFactors = FALSE)
udc.chunkcenters <- read.csv("~/udc/udc.chunkscenters.csv", stringsAsFactors=FALSE)
udc.sessions <- read.csv("~/udc/udc.sessions2.csv", stringsAsFactors = FALSE)
udc.sessionssplit.1 <- read.csv("~/udc/udc.splittedsessions.csv", stringsAsFactors=FALSE)
udc.sessionssplit <- read.csv("~/udc/udc.splittedsessions2.csv", stringsAsFactors=FALSE)
udc.sessionscenters <- read.csv("~/udc/udc.sessioncenters.csv", stringsAsFactors=FALSE)

abb.chunks <- read.csv("~/abb/abb.chunks.csv", stringsAsFactors = FALSE)
abb.chunkcenters <- read.csv("~/abb/abb.chunkscenters.csv", stringsAsFactors=FALSE)
abb.sessions <- read.csv("~/abb/abb.sessions2.csv", stringsAsFactors = FALSE)
abb.sessionssplit.1 <- read.csv("~/abb/abb.splittedsessions.csv", stringsAsFactors=FALSE)
abb.sessionssplit <- read.csv("~/abb/abb.splittedsessions2.csv", stringsAsFactors=FALSE)
abb.sessionscenters <- read.csv("~/abb/abb.sessioncenters.csv", stringsAsFactors=FALSE)


save.plot <- function(plot, name, w, h){
  ggsave(paste(name,".pdf",sep=""), width = w, height = h, units="cm")
}


silhouette.analysis.sessions <- function(sessions, sessions.labels){
  set.seed(123)
  dis <- dist(sessions[,c(1:12)])
  s <- silhouette(sessions$label, dis)
  sdf <-s[, 1:3]
  sdf <-data.frame(sdf)
  sdf$cluster <- sessions$label
  sdf <- sdf[sdf$cluster %in% sessions.labels,]
  nl <- c("Type A", "Type B", "Type C", "Type D", "Type E")
  for(i in c(1:length(sessions.labels))){
    sdf[sdf$cluster == sessions.labels[i],]$cluster <- nl[i]
  }
  sdf$cluster <- factor(sdf$cluster, levels = nl)
  sdf <- sdf[order(sdf$cluster, -sdf$sil_width),]
  sdf$name <- as.factor(1:nrow(sdf))
  cat("Average silhouette value: ", mean(sdf$sil_width), "\n")
  sdf
  
}

silhouette.analysis.chunks <- function(chunks, chunks.labels){
  set.seed(123)
  dis <- dist(chunks[,c(16:25)])
  s <- silhouette(chunks$label, dis)
  sdf <-s[, 1:3]
  sdf <-data.frame(sdf)
  sdf$cluster <- chunks$label.c
  sdf <- sdf[sdf$cluster %in% chunks.labels,]
  sdf$cluster <- factor(sdf$cluster, levels = chunks.labels)#as.factor(sdf$cluster)
  sdf <- sdf[order(sdf$cluster, -sdf$sil_width),]
  sdf$name <- as.factor(1:nrow(sdf))
  cat("Average silhouette value: ", mean(sdf$sil_width), "\n")
  sdf
  
}


plot.silhouette.chunks <- function(data, data.name, cbPalette){
  plot <- ggplot(data, aes(x=name, y=sil_width, color=cluster, fill=cluster)) + 
          geom_bar(stat="identity") + ylim(c(NA,1)) + theme_few() +  scale_color_manual(values=cbPalette) +
          scale_fill_manual(values=cbPalette) + theme(axis.text.x = element_blank(), axis.ticks.x = element_blank()) +
          labs(x="Observations", y="Silhouette width", fill="Cluster (activity)", color="Cluster (activity)") 
  
  save.plot(plot, paste(data.name, "silhouette_chunks", sep="_"), 21, 13)
}

plot.silhouette.sessions <- function(data, data.name, cbPalette){
  plot <- ggplot(data, aes(x=name, y=sil_width, color=cluster, fill=cluster)) + 
    geom_bar(stat="identity") + ylim(c(NA,1)) + theme_few() + 
    theme(axis.text.x = element_blank(), axis.ticks.x = element_blank()) +
    labs(x="Observations", y="Silhouette width", fill="Cluster (sessions)", color="Cluster (sessions)") 
  
  save.plot(plot, paste(data.name, "silhouette_sessions", sep="_"), 21, 13)
}

plot.phases.by.session.type <- function(data, data.name, plot.name, width, height, cbPalette){
  plot <- ggplot(data, aes(x=phase, y=value, color=activity)) + 
          geom_point(size=4, alpha=0.8) + geom_line(aes(group=activity), size=1.3, alpha=0.8) + 
          labs(x="Phases", y="Average Proportion", color="Activity", title=paste("Proportion of activities by session phase in",data.name)) +
          scale_x_continuous(breaks = 1:3) +
          facet_grid(label ~ .) + theme_few() + scale_color_manual(values=cbPalette) + 
          theme(legend.position="bottom") + theme(panel.margin = unit(1.5, "lines"))
  save.plot(plot, plot.name, width, height)
}


plot.phases.by.session.type.log <- function(data, data.name, plot.name, width, height, cbPalette){
  plot <- ggplot(data, aes(x=phase, y=log(value*100), color=activity)) + 
    geom_point(size=4) + geom_line(aes(group=activity), size=1.3) + 
    labs(x="Phases", y="log(Average Proportion)", color="Activity", title=paste("Proportion of activities by session phase in",data.name)) +
    scale_x_continuous(breaks = 1:3) + #scale_y_continuous(limits=c(-1,)) +
    facet_grid(label ~ .) + theme_few() +  scale_color_manual(values=cbPalette) + theme(legend.position="bottom") +
    theme(panel.margin = unit(1.5, "lines"))
  save.plot(plot, plot.name, width, height)
}


pipeline <- function(chunks, sessions, sessionssplit, sessionssplit.1, chunks.label, sessions.label, plot1.name, data.name, cbPalette){
  #chunks$label.c <- factor(chunks$label.c, levels = chunks.label.c)
  sessionssplit$activity <- factor(sessionssplit$activity, levels = chunks.label)
  
  cat("Analyzing silhouette of chunks...\n")
  chunkstemp <- chunks[chunks$label.c %in% chunks.label,]
  sdf <- silhouette.analysis.chunks(chunkstemp[1:(nrow(chunkstemp)*0.60),], chunks.label)
  plot.silhouette.chunks(sdf, data.name, cbPalette)
  
  cat("Analyzing silhouette of sessions...\n")
  sdf.sessions <- silhouette.analysis.sessions(sessionssplit.1[sessionssplit.1$label %in% sessions.label,], sessions.label )
  plot.silhouette.sessions(sdf.sessions, data.name, cbPalette)
  
  cat("| Number of sessions:\t\t", nrow(sessions))
  cat("\n| Number of users:\t\t", length(unique(sessions$user)))
  cat("\n| Average session length:\t", mean(sessions$size_ts))
  cat("\n| Number of usable sessions:\t", nrow(sessions[sessions$label %in% c("Type A", "Type B", "Type C", "Type D", "Type E"),]))
  cat("\n| Number of sessions by type:\n")
  s <- summary(as.factor(sessions[sessions$label %in% c("Type A", "Type B", "Type C", "Type D", "Type E"),]$label))
  cat("|\t Type A:", s[1])
  cat("\n|\t Type B:", s[2])
  cat("\n|\t Type C:", s[3])
  cat("\n|\t Type D:", s[4])
  cat("\n|\t Type E:", s[5])
  session.types <- c("Type A", "Type B", "Type C", "Type D", "Type E")
  cat("\n| Number of unique users by session type:")
  for(i in session.types){
    cat("\n|\t", i, ": ", length(unique(sessions[sessions$label == i,]$user)))
  }
  cat("\n| Number of chunks:\t", nrow(chunks))
  cat("\n| Number of chunks by type:")
  chunks.labels <- unique(chunks$label.c)
  for(i in chunks.labels){
    cat("\n|\t", i, ": ", nrow(chunks[chunks$label.c == i,]))
  }
  cat("\n")
  
  plot.phases.by.session.type.log(sessionssplit, data.name, plot.name = paste(data.name,"phases_log", sep="_"),
                                  width = 14, height = 24, cbPalette)
  
}

# ABB
cat("Statistics ABB data")
chunk.labels <- c("Programming", "Debugging", "Version", "Navigation")
session.labels <- c(27, 4, 11, 13, 25)
color.pallete <- c("#7188cc", "#c76552","#61a275","#4D4D4D","#c19046")
pipeline(abb.chunks, abb.sessions, abb.sessionssplit, abb.sessionssplit.1, chunk.labels, session.labels, "abb.phases", "ABB", color.pallete)


# UDC
cat("Statistics UDC data")
chunk.labels <- c("Programming", "Debugging", "Version", "Navigation")
session.labels <- c(78, 64, 23, 62, 37)
color.pallete <- c("#7188cc", "#d04d3f","#61a275","#4D4D4D","#cf5f9e")
pipeline(udc.chunks, udc.sessions, udc.sessionssplit, udc.sessionssplit.1, chunk.labels, session.labels, "udc.phases", "UDC", color.pallete)


