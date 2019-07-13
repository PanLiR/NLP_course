#从北京地铁的百度百科中爬出其源码，并解码成文本格式
from urllib import request
url = "http://www.bjsubway.com/station/zjgls/#"
header = {"User-Agent":
"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:67.0) Gecko/20100101 Firefox/67.0"}

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

rq = request.Request(url, headers = header)
response1 = request.urlopen(rq)
url_str = response1.read().decode("GBK") #将获取的源码解码成文本格式

#利用正则表达式获取所需信息
import re

#先获取地铁线路名称
route_judge = r'<td.*>([\d\u4E00-\u9FA5\W]+)相邻站间距信息统计表</td>'
routes_pattern = re.compile(route_judge)
routes = routes_pattern.findall(url_str)

#获取每个站点名称在源码文本中对应点索引
route_indexes = []
for route in routes:
    route_indexes.append(url_str.find(route+"相邻站间距信息统计表")) #因为有的线路名称在源码文本中出现不止一次，故加上后缀确保唯一性
route_indexes.append(len(url_str)) #在索引表中加上最后一个元素的索引，便于后续操作

#再获取每条线路对应的站点
station_judge = r'<th>([\u4E00-\u9FA5]+)\W+([\u4E00-\u9FA5]+)</th>'
stations_pattern = re.compile(station_judge)
route_stations = {}
for i in range(len(routes)):
    route_stations[routes[i]] = stations_pattern.findall(url_str[route_indexes[i]:route_indexes[i+1]])

#上面得到的字典中线路对应的是由站点对构成的列表，剔除重复值，重新建立列表
for route in route_stations:
    stations = []
    for station_pair in route_stations[route]:
        stations.append(station_pair[0])
    stations.append(station_pair[1])
    route_stations[route] = stations

#构建地铁线路图，找到每个站点相邻的站点
from collections import defaultdict
station_graph = defaultdict(list)
for route in route_stations:
    for i in range(len(route_stations[route])):
        if i == 0: #如果是线路的第一个站点，则将第二个站点加入第一个站点的相邻站列表
            station_graph[route_stations[route][i]] += [route_stations[route][1]]
        elif i == len(route_stations[route]) - 1: #如果是线路的最后一个站点，则将倒数第二个站点加入其相邻站列表
            station_graph[route_stations[route][i]] += [route_stations[route][-2]]
        else: #如果是线路中间的站点，则将前后两个站点加入其相邻站列表
            station_graph[route_stations[route][i]] += [route_stations[route][i-1], route_stations[route][i+1]]

#上述地铁线路图中，站点对应的相邻站存在重复项，将重复项剔除
for station in station_graph:
    station_adjacent = set(station_graph[station])
    station_graph[station] = list(station_adjacent)

#找到每两个站点之间的距离
distance_judge = r'<th>([\u4E00-\u9FA5]+)\W+([\u4E00-\u9FA5]+)</th>[\r\n\s]+<td.*>(\d+)</td>'
pattern_distance = re.compile(distance_judge)
station_distance = pattern_distance.findall(url_str)

#上面将获取的站点及其距离组建成元组，这里将其提取出来建立字典，并对每个站点建立单独的字典，其中相邻站点作为键，距离作为值
station_distance_dic = defaultdict(dict)
for m in station_distance:
    station_distance_dic[m[0]][m[1]] = float(m[2])
    station_distance_dic[m[1]][m[0]] = float(m[2])

#定义函数，给定任意起点、终点和地图，找到所有可能的路线图，根据选择的方案给出最优路线
def search(start, destination, map, sort_candidate):
    pathes =[[start]]
    visited =[]
    pathes_candidate = []

    while pathes:
        path = pathes.pop()
        frontier = path[-1]
        if frontier in visited:
            continue

        for station in map[frontier]:
            if station in visited:
                continue
            new_path = path + [station]

            if station == destination:
                pathes_candidate.append(new_path)

            pathes.append(new_path)
        visited.append(frontier)

    print(pathes_candidate)
    pathes_candidate = sort_candidate(pathes_candidate)
    return "-> ".join(pathes_candidate[0])

#定义函数，找出每条路线的路程
def get_path_distance(path):
    distance_sum = 0
    for i in range(len(path)-1):
        distance_sum += station_distance_dic[path[i]][path[i+1]]

    return distance_sum

#定义函数，找出站数最少的路线
def stations_min(pathes):
    return sorted(pathes, key=len)

#定义函数，找出路程最短的路线
def distance_min(pathes):
    return sorted(pathes, key=get_path_distance)

'''函数search(start, destination, map, sort_candidate)在找出路程最短的线路时，是采用局部最优的解法，为考虑全面，建立函数
search_shortest_route(start, destination, map)'''
def search_shortest_route(start, destination, map):
    pathes = {}
    successors = []
    distance = {}

    for station in station_graph[start]:
        distance[station] = station_distance_dic[start][station]
        successors.append(station)
        pathes[station] = [start, station]

    for successor in successors:
        for station in station_graph[successor]:
            if station in distance:
                if distance[station] > distance[successor] + station_distance_dic[successor][station]:
                    distance[station] = distance[successor] + station_distance_dic[successor][station]
                    pathes[station] = pathes[successor] + [station]
            else:
                distance[station] = distance[successor] + station_distance_dic[successor][station]
                pathes[station] = pathes[successor] + [station]
                successors.append(station)
            if destination in distance and distance[destination] <= distance[station]:
                del successors[-1]

    return "-> ".join(pathes[destination])


path1 = search('苹果园', '宋家庄', station_graph, stations_min)
path2 = search_shortest_route('苹果园', '宋家庄', station_graph)

print(path1)
print(path2)


