from ciscoconfparse import CiscoConfParse

#parse.find_objects
#obj.re_search_children
#parse.find_objects_wo_child
#global_obj.re_match_typed
#ntf_obj.re_match_iter_typed

#ciscoconfparse.CiscoConfParse Object
'''
class ciscoconfparse.CiscoConfParse(config='', comment='!', debug=False, factory=False, linesplit_rgx='\r*\n+', ignore_blank_lines=True, syntax='ios')

append_line(linespec)
atomic()
commit()
convert_braces_to_ios(input_list, stop_width=4)
delete_lines(linespec, exactmatch=False, ignore_ws=False)


'''

#VLAN9がアサインされているIFを抽出
def main():
    parse = CiscoConfParse('cat.txt')
    for obj in parse.find_objects(r"interface Giga"):
        if obj.re_search_children(r"switchport access vlan 9"):
            print(obj.text)

def Get_Conf():
    parse = CiscoConfParse('conf.txt')

    #ホスト名の値だけ取得したい
    global_obj = parse.find_objects(r'^hostname')[0]
    print(global_obj)
    hostname = global_obj.re_match_typed(r'^hostname\s+(\S+)', default='')
    print(hostname)

    #反復処理して見つかった最初の値を返す
    hostname = parse.re_match_iter_typed(r'^hostname\s+(\S+)', default='')
    print(hostname)

    #VLAN10のHSRP IPアドレスを取得
    intf_obj = parse.find_objects(r'^interface\s+Vlan10$')[0]
    hsrp_ip = intf_obj.re_match_iter_typed(r'standby\s10\sip\s(\S+)', default='')
    print(hsrp_ip)

    #VLAN10のARPタイムアウト値を取得(intで返す)
    intf_obj = parse.find_objects(r'^interface\s+Vlan10$')[0]
    arp_timeout = intf_obj.re_match_iter_typed(r'arp\s+timeout\s+(\d+)', result_type=int, default=4*3600)
    print(arp_timeout)

    #要素が見つからなかった場合のデフォルト値の指定
    intf_obj = parse.find_objects(r'^interface\s+Vlan20$')[0]
    arp_timeout = intf_obj.re_match_iter_typed(r'arp\s+timeout\s+(\d+)', result_type=int, untyped_default=True, default='__no_explicit_value__')
    print(arp_timeout)

    retval = list()
    HELPER_REGEX = r'ip\s+helper-address\s+(\S+)$'
    NO_MATCH = '__no_match__'

    #VLAN10のDHCPヘルパーアドレス（複数）を返す処理
    for intf_obj in parse.find_objects(r'^interface\s+Vlan10$'):
        for child_obj in intf_obj.children:  # Iterate over intf children
            val = child_obj.re_match_typed(HELPER_REGEX, default=NO_MATCH)
            if val!=NO_MATCH:
                retval.append(val)
    
    print(retval)

def standardize_intfs(parse):

    ## Search all switch interfaces and modify them
    #
    # r'^interface.+?thernet' is a regular expression, for ethernet intfs
    for intf in parse.find_objects(r'^interface.+?thernet'):
        has_stormcontrol = intf.has_child_with(r' storm-control broadcast')
        is_switchport_access = intf.has_child_with(r'switchport mode access')
        is_switchport_trunk = intf.has_child_with(r'switchport mode trunk')

        ## Add missing features
        if is_switchport_access and (not has_stormcontrol):
            intf.append_to_family(' storm-control action trap')
            intf.append_to_family(' storm-control broadcast level 0.4 0.3')

        ## Remove dot1q trunk misconfiguration...
        elif is_switchport_trunk:
            intf.delete_children_matching('port-security')


def Audit():
    ## Parse the config
    parse = CiscoConfParse('conf.txt')

    for i in range(25):
    ## Add a new switchport at the bottom of the config...
        parse.append_line('interface FastEthernet0/' + str(i))
        parse.append_line(' switchport')
        parse.append_line(' switchport mode access')
        parse.append_line('!')
        parse.commit()     # commit() **must** be called before searching again

    ## Search and standardize the interfaces...
    standardize_intfs(parse)
    parse.commit()     # commit() **must** be called before searching again

    ## I'm illustrating regular expression usage in has_line_with()
    if not parse.has_line_with(r'^service\stimestamp'):
        ## prepend_line() adds a line at the top of the configuration
         parse.prepend_line('service timestamps debug datetime msec localtime show-timezone')
         parse.prepend_line('service timestamps log datetime msec localtime show-timezone')

    ## Write the new configuration
    parse.save_as('conf3.txt')

#Configの変更
def Modify_Conf():
    parse = CiscoConfParse('cat.txt')

    #特定のI/FのVLAN番号を変更する
    #例：10、12番ポートのVLAN番号を変更する
    for i in range(25):
        if ( i == 10 ):
            for intf in parse.find_objects(r'^interface GigabitEthernet0/' + str(i)):
                if ( intf.has_child_with(r' switchport access vlan')):
                    intf.delete_children_matching(r' switchport access vlan')
                    parse.insert_after(r'^interface GigabitEthernet0/' + str(i), insertstr=' switchport access vlan 999', exactmatch=False, ignore_ws=False, atomic=False)
                    parse.commit()

        elif ( i == 12 ):
             for intf in parse.find_objects(r'^interface GigabitEthernet0/' + str(i)):
                if ( intf.has_child_with(r' switchport access vlan')):
                    intf.delete_children_matching(r' switchport access vlan')
                    parse.insert_after(r'^interface GigabitEthernet0/' + str(i), insertstr=' switchport access vlan 999', exactmatch=False, ignore_ws=False, atomic=False)
                    parse.commit()           

    #新規ファイルに書き込み
    parse.save_as('cat2.txt')

if __name__ == '__main__':
    #Configの変更
    Modify_Conf()
    