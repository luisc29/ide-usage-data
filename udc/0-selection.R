#DATA SELECTION

install.packages("assertthat");
install.packages("bigrquery");
install.packages("lubridate");
install.packages("ggplot2")
install.packages("foreach")
install.packages("doSNOW")
install.packages("plyr")
install.packages("dplyr")

library(bigrquery)
library(plyr)
library(dplyr)
library(ggplot2)
library(lubridate)
library(foreach)
library(doSNOW)
library(grid)

# ------------------- QUERIES --------------------------------------------------------

#ID del proyecto
project <- "apt-reality-88002";
project <- "udc-data"

sql <- "select userId,what,kind,bundleId,description, MSEC_TO_TIMESTAMP(time) as datetime from [udc-data:udc.all]
where what!='started' and what!='stopped' 
and (userId=763034 or userId=1746564 or userId=785972 
or userId=106382 or userId=1326688 or userId=890959
or userId=536010 or userId=1641673 or userId=1812107 or userId=758588 
or userId=825164 or userId=660007 or userId=771585 or userId=121645 or userId=337183 
or userId=430334 or userId=700027 
or userId=111025 or userId=126917 or userId=734706)"

#Consulta con seleccion aleatoria de usuarios
sql <- "select userId,what,kind,bundleId,description, MSEC_TO_TIMESTAMP(time) as datetime 
from [udc-data:udc.all] a
where what!='started' and what!='stopped' 
and userId in (select userId 
FROM [udc-data:udc.all] b 
WHERE rand() < 100000/2323233101 group by userId limit 2000)"


sql <- "select userId,what,kind,bundleId,description, MSEC_TO_TIMESTAMP(time) as datetime 
from [udc-data:udc.all] a
where what!='started' and what!='stopped' 
and userId in ( select userId from (select userId, count(userId) as count 
from [udc-data:udc.all] b
where what!='started' and what!='stopped' 
group by userId
order by count desc
limit 50)
)"

data <- query_exec(sql,project,max_pages=Inf)
