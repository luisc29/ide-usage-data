install.packages("ggplot2")
install.packages("gridExtra")

library(ggplot2)
library(grid)
library(gridExtra)

bp <- function(sessions, col.num, t = c(0,3,6,9), x.labels , y.lim, y.lab, x.lab, color){
  a1 <- sessions[sessions$n_inte == t[1], col.num]
  a2 <- sessions[sessions$n_inte > t[1] & sessions$n_inte <= t[2], col.num]
  a3 <- sessions[sessions$n_inte > t[2] & sessions$n_inte <= t[3], col.num]
  a4 <- sessions[sessions$n_inte > t[3] & sessions$n_inte <= t[4], col.num]
  a5 <- sessions[sessions$n_inte > t[4], col.num]
  boxplot(a1,a2,a3,a4,a5, ylim = c(0,y.lim), names=x.labels, ylab=y.lab, border=color, xlab=x.lab)
}



nrow(sessions)
sessions <- sessions[sessions$n_edition > 0 ,]
sessions <- sessions[sessions$n_inte < 500,]

thresholds <- quantile(sessions$n_inte)

labels <- c("none", "[1-7]", "[7-13]", "[13-26]",">26")
#edits per minute
bp(sessions,20,t=thresholds[1:4], labels, 20, "Edits / minute", "Interruptions","red")

#selections per minute
bp(sessions,21,t=thresholds[1:4], labels, 20, "Selections / minute", "Interruptions","blue")

#edit ratio
bp(sessions,22,t=thresholds[1:4], labels, 1, "Edit ratio", "Interruptions","black")

#####3

#18, 111, 113
v1 <- sessions[113,]$inte.v[[1]]
v1 <- v1[1:length(v1)-1]
v2 <- sessions[113,]$focus.v[[1]]
v2 <- v2[1:length(v2)-1]


data.plot <- data.frame(inte = v1, focus = c(v2,rep(0,length(v1)-length(v2))), index = c(1:length(v1)))
g1 <- ggplot(data.plot,aes(index)) + geom_line(aes(y=inte)) 
g2 <- ggplot(data.plot,aes(index)) + geom_line(aes(y=focus),color="red")
grid.arrange(g1,g2,ncol=1)
