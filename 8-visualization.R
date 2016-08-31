library(plyr)
library(dplyr)
library(tidyr)
library(ggplot2)
library(ggthemes)
library(grid)
library(gridExtra)
library(clustertend)
library(cluster)

# load the data
udc.chunks <- read.csv("~/udc/udc.chunks.csv", stringsAsFactors = FALSE)
udc.chunkcenters <- read.csv("~/udc/udc.chunkscenters.csv", stringsAsFactors=FALSE)
udc.sessions <- read.csv("~/udc/udc.sessions2.csv", stringsAsFactors = FALSE)
udc.sessionssplit <- read.csv("~/udc/udc.splittedsessions2.csv", stringsAsFactors=FALSE)
udc.sessionscenters <- read.csv("~/udc/udc.sessioncenters.csv", stringsAsFactors=FALSE)

abb.chunks <- read.csv("~/abb/abb.chunks.csv", stringsAsFactors = FALSE)
abb.chunkcenters <- read.csv("~/abb/abb.chunkscenters.csv", stringsAsFactors=FALSE)
abb.sessions <- read.csv("~/abb/abb.sessions2.csv", stringsAsFactors = FALSE)
abb.sessionssplit <- read.csv("~/abb/abb.splittedsessions2.csv", stringsAsFactors=FALSE)
abb.sessionscenters <- read.csv("~/abb/abb.sessioncenters.csv", stringsAsFactors=FALSE)


save.plot <- function(plot, name, w, h){
  png(paste(name,".png",sep=""), width = w, height = h, units="px")
  #png(paste(name,".png",sep=""))
  print(plot)
  
  ggsave(paste(name,".pdf",sep=""), width = 14, height = 24, units="cm")
  dev.off()
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
    geom_point(size=4, alpha=0.8) + geom_line(aes(group=activity), size=1.3, alpha=0.8) + 
    labs(x="Phases", y="log(Average Proportion)", color="Activity", title=paste("Proportion of activities by session phase in",data.name)) +
    scale_x_continuous(breaks = 1:3) + #scale_y_continuous(limits=c(-1,)) +
    facet_grid(label ~ .) + theme_few() +  scale_color_manual(values=cbPalette) + theme(legend.position="bottom") +
    theme(panel.margin = unit(1.5, "lines"))
  save.plot(plot, plot.name, width, height)
}


pipeline <- function(chunks, sessions, sessionssplit, chunks.label, plot1.name, data.name, cbPallete){
  chunks$label.c <- factor(chunks$label.c, levels = chunks.label)
  sessionssplit$activity <- factor(sessionssplit$activity, levels = chunks.label)
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
  plot.phases.by.session.type(sessionssplit, data.name, plot.name = paste(data.name,"phases", sep="_"), 
                              width = 400, height = 900, cbPallete)
  plot.phases.by.session.type.log(sessionssplit, data.name, plot.name = paste(data.name,"phases_log", sep="_"),
                                  width = 400, height = 900, cbPallete)
  
}

# ABB
cat("Statistics ABB data")
chunk.labels <- c("Programming", "Debugging", "Version", "Navigation", "Testing")
color.pallete <- c("#7188cc", "#c76552","#61a275","#4D4D4D","#c19046")
pipeline(abb.chunks,  abb.sessions, abb.sessionssplit, chunk.labels, "abb.phases", "ABB", color.pallete)


# UDC
cat("Statistics UDC data")
chunk.labels <- c("Programming", "Debugging", "Version", "Navigation", "Refactoring")
color.pallete <- c("#7188cc", "#d04d3f","#61a275","#4D4D4D","#cf5f9e")
pipeline(udc.chunks, udc.sessions, udc.sessionssplit, chunk.labels, "udc.phases", "UDC", color.pallete)


#### Silhouette analysis

abb.chunks <- read.csv("~/abb/abb.chunks_a.csv", stringsAsFactors = FALSE)
abb.centers <- read.csv("~/abb/Babb.chunkscenters_a.csv", stringsAsFactors = FALSE)
subset <- abb.chunks[1:12000,c(16:25)]
set.seed(123)

d <- dist(subset)
s <- silhouette(abb.chunks[1:12000,]$label2, d)
temp <-s[, 1:3]
temp2 <-data.frame(temp)
temp2 <- temp2[order(temp2$cluster, -temp2$sil_width),]
quantile(temp2$sil_width)

fviz_silhouette(s)
ggplot(temp2[temp2$cluster %in% c(0,1,2,3),], aes(x=sil_width)) + geom_histogram()+ facet_grid(. ~ cluster)
