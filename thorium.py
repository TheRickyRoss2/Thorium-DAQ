__author__ = "Ric Rodriguez"
__email__ = "therickyross2@gmail.com"
__project__ = "Thorium DAQ"

import configparser

if __name__ == "__main__":
    print("""Welcome to
    
 ________  __                            __                         
/        |/  |                          /  |                        
$$$$$$$$/ $$ |____    ______    ______  $$/  __    __  _____  ____  
   $$ |   $$      \  /      \  /      \ /  |/  |  /  |/     \/    \ 
   $$ |   $$$$$$$  |/$$$$$$  |/$$$$$$  |$$ |$$ |  $$ |$$$$$$ $$$$  |
   $$ |   $$ |  $$ |$$ |  $$ |$$ |  $$/ $$ |$$ |  $$ |$$ | $$ | $$ |
   $$ |   $$ |  $$ |$$ \__$$ |$$ |      $$ |$$ \__$$ |$$ | $$ | $$ |
   $$ |   $$ |  $$ |$$    $$/ $$ |      $$ |$$    $$/ $$ | $$ | $$ |
   $$/    $$/   $$/  $$$$$$/  $$/       $$/  $$$$$$/  $$/  $$/  $$/  
    """)
    print("By: Ric Rodriguez")
    print("For support or bug report submission: Please email Ric at therickyross2@gmail.com")

    with open("config.ini") as settings:
        daq_settings = settings.read()
    config = configparser.RawConfigParser(allow_no_value=True)
    config.read_file(open("config.ini"))

    for section in config.sections():
        print("Section: {}".format(section))
        for options in config.options(section):
            print("x {}::{}::{}".format(options, config.get(section, options), str(type(options))))
    print(config.get('caen', 'iset'))
    print(config.getboolean('lecroy', 'enable_channel1'))
