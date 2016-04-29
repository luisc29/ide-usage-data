install.packages("ggplot2")

library(ggplot2)

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
