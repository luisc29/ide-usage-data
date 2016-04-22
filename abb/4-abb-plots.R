install.packages("ggplot2")

library(ggplot2)

bp <- function(sessions, col.num, t = c(0,3,6,9), x.labels , y.lim, y.lab, x.lab, color){
  a1 <- sessions[sessions$num_inte == t[1], col.num]
  a2 <- sessions[sessions$num_inte > t[1] & sessions$num_inte <= t[2], col.num]
  a3 <- sessions[sessions$num_inte > t[2] & sessions$num_inte <= t[3], col.num]
  a4 <- sessions[sessions$num_inte > t[3] & sessions$num_inte <= t[4], col.num]
  a5 <- sessions[sessions$num_inte > t[4], col.num]
  boxplot(a1,a2,a3,a4,a5, ylim = c(0,y.lim), names=x.labels, ylab=y.lab, border=color, xlab=x.lab)
}



nrow(sessions)
sessions <- sessions[sessions$edit_text > 0 & sessions$text_nav > 0 & sessions$high_nav >0,]
sessions <- sessions[sessions$num_inte < 500,]

thresholds <- quantile(sessions$num_inte)

labels <- c("none", "[1-7]", "[7-13]", "[13-26]",">26")
#edits per minute
bp(sessions,23,t=thresholds[1:4], labels, 10, "Edits / minute", "Interruptions","red")

#selections per minute
bp(sessions,24,t=thresholds[1:4], labels, 20, "Selections / minute", "Interruptions","blue")

#edit ratio
bp(sessions,25,t=thresholds[1:4], labels, 1, "Edit ratio", "Interruptions","black")
