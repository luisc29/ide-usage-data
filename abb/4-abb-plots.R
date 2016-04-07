install.packages("ggplot2")

library(ggplot2)

bp <- function(df = sessions, col.num, t = c(0,3,6,9), x.labels , y.lim, y.lab, x.lab, color){
  a1 <- sessions[sessions$num_inte == t[1], col.num]
  a2 <- sessions[sessions$num_inte > t[1] & sessions$num_inte <= t[2], col.num]
  a3 <- sessions[sessions$num_inte > t[2] & sessions$num_inte <= t[3], col.num]
  a4 <- sessions[sessions$num_inte > t[3] & sessions$num_inte <= t[4], col.num]
  a5 <- sessions[sessions$num_inte > t[4], col.num]
  boxplot(a1,a2,a3,a4,a5, ylim = c(0,y.lim), names=x.labels, ylab=y.lab, border=color, xlab=x.lab)
}

thresholds <- quantile(sessions$num_inte)

#edits per minute
bp(sessions,5,t=thresholds[1:4], c("none", "[1-12]", "[13-20]", "[21-41]",">41"), 20, "Edits / minute", "Interruptions","red")

#selections per minute
bp(sessions,6,t=thresholds[1:4], c("none", "[1-12]", "[13-20]", "[21-41]",">41"), 20, "Selections / minute", "Interruptions","blue")

#edit ratio
bp(sessions,7,t=thresholds[1:4], c("none", "[1-12]", "[13-20]", "[21-41]",">41"), 1, "Edit ratio", "Interruptions","black")
