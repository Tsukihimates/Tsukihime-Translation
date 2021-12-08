#!/usr/bin/env python3
import os
import platform
import jpype
import asposecells
jpype.startJVM()
from asposecells.api import *

def create_csv(fileJP,fileEN,lay):
    with open(fileJP, "r+", encoding="utf-8") as fJP:
        dataJP = fJP.read().split("\n")
        if dataJP[-1] == "":
            dataJP = dataJP[:-1]
    with open(fileEN, "r+", encoding="utf-8") as fEN:
        dataEN = fEN.read().split("\n")
        if dataEN[-1] == "":
            dataEN = dataEN[:-1]

    if (len(dataJP) == len(dataEN)):

        if platform.system() == "Windows":
            splitChar = "\\"
        else:
            splitChar = "/"

        nameWb = fileJP.split(splitChar)[-1].split(".")[0]

        os.chdir("XLSX")

        workbook = open(nameWb+".xlsx", "w+", encoding="utf-8")
        workbook.close()

        wb = Workbook(nameWb+".xlsx")

        if lay == "1":
            for i in range(len(dataJP)):
                wb.getWorksheets().get(0).getCells().get("A"+str(i+1)).putValue(dataJP[i])
                wb.getWorksheets().get(0).getCells().get("B"+str(i+1)).putValue(dataEN[i])

            ws = wb.getWorksheets().get(0)

            ws.autoFitColumn(0)
            ws.autoFitColumn(1)
        else:
            i = 0
            j = 1
            while i < len(dataJP):
                if dataJP[i] == dataEN[i]:
                    wb.getWorksheets().get(0).getCells().get("A"+str(j)).putValue(dataEN[i])
                    j += 1
                    i += 1
                else:
                    wb.getWorksheets().get(0).getCells().get("A"+str(j)).putValue(dataJP[i])
                    wb.getWorksheets().get(0).getCells().get("A"+str(j+1)).putValue(dataEN[i])
                    j += 2
                    i += 1

            ws = wb.getWorksheets().get(0)

            ws.autoFitColumn(0)

        wb.save(nameWb+".xlsx")

        os.chdir("..")

if __name__ == "__main__":

    if os.path.exists("EN") and os.path.exists("JP"):

        layout = input("Choose your layout (1 for side-by-side, 2 for line-by-line): ")

        if not os.path.exists("XLSX"):
            os.mkdir("XLSX")

        for root, dirs, files in os.walk(os.getcwd()+"/JP"):
            for file in files:
                create_csv(os.getcwd()+"/JP/"+file,os.getcwd()+"/EN/"+file,layout)
                print(file+" done.")
