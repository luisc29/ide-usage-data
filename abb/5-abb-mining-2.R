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

decomposed <- read.csv("~/abb/decomposed_ts.csv", stringsAsFactors = FALSE)
chunk.centers <- read.csv("~/abb/chunks_centers.csv", stringsAsFactors=FALSE)
sessions.centers <- read.csv("~/abb/sessions_centers.csv", stringsAsFactors=FALSE)

# set the labels manually after observing the positions of the centers

decomposed.agg <- aggregate(decomposed, by = list(decomposed$id), FUN = length)
valid.sessions <- decomposed.agg[decomposed.agg$n_events > 10,]$Group.1
decomposed <- decomposed[decomposed$id %in% valid.sessions,]
decomposed$label.c <- unlist(lapply(decomposed$label, function(x){
  chunk.centers[chunk.centers$X == x,]$label[1]
}))

sessions$label.c <- unlist(lapply(sessions$label, function(x){
  sessions.centers[sessions.centers$X == x,]$label[1]  
}))

chunk2 <- function(x,n) split(x, cut(seq_along(x), n, labels = FALSE)) 
split.equal.chunks <- function(s, size, chosen.labels){
  n.labs <- length(chosen.labels)
  res <- data.frame(label = character(size*n.labs))
  labels <- character(size*n.labs)
  segments <- numeric(size*n.labs)
  counts <- numeric(size*n.labs)
  for (i in 1:length(s)) {  # for every session
    d <- as.factor(decomposed[decomposed$id == s[i],]$label.c)
    d.splitted <- chunk2(d, size)  # split it into five chunks
    
    for (j in 0:(length(chosen.labels)-1)){  # for each type
      l <- chosen.labels[j+1]
      for (k in 1:size){  # count how many segments of that type exist on every segment 
        current.segment <- d.splitted[[k]][d.splitted[[k]] == l]
        len <- length(current.segment)
        labels[(j*size) + k ] <- l
        segments[(j*size) + k ] <- k
        counts[(j*size) + k  ] <- counts[(j*size) + (k)] + len
      }
    }
  }
  res$label <- labels
  res$segment <- segments
  res$count <- counts
  
  # normalize the counts
   for (j in chosen.labels){
     m <- max(res[res$label == j,]$count)
     res[res$label == j,]$count <- res[res$label == j,]$count / m
   }
  res
}


# amount of chunks by type
summary(as.factor(decomposed$label.c))
chosen.labels <- c("programming","debugging","version-control","testing")
decomposed.chunks <- split.equal.chunks(valid.sessions, 10, chosen.labels)
decomposed.chunks$label <- factor(decomposed.chunks$label, levels = chosen.labels)
ggplot(decomposed.chunks, aes(x=segment, y=count, color=label)) + geom_point(size=5) + scale_x_continuous(breaks = 1:10) + 
  geom_line(size=2, alpha=0.6) + theme_hc() +  scale_colour_few() + labs(x="Chunk", y="Count (normalized)", color="Type")

cor(decomposed.chunks[decomposed.chunks$label == "programming",]$count, decomposed.chunks[decomposed.chunks$label == "debugging",]$count)

