function(doc) {
    
    var time_zones = {
        'Kinshasa': 'Africa',
        'Regina': 'America',
        'Ponape': 'Pacific',
        'Kiev': 'Europe',
        'Paris': 'Europe',
        'Oslo': 'Europe',
        'Dar_es_Salaam': 'Africa',
        'Addis_Ababa': 'Africa',
        'Johannesburg': 'Africa',
        'Fortaleza': 'America',
        'Aruba': 'America',
        'Calcutta': 'Asia',
        'Beirut': 'Asia',
        'Nicosia': 'Asia',
        'Simferopol': 'Europe',
        'Bahrain': 'Asia',
        'Tegucigalpa': 'America',
        'Santiago': 'America',
        'Cape_Verde': 'Atlantic',
        'Azores': 'Atlantic',
        'Phnom_Penh': 'Asia',
        'Bangui': 'Africa',
        'Berlin': 'Europe',
        'Malabo': 'Africa',
        'Buenos_Aires': 'America',
        'Guatemala': 'America',
        'Sao_Tome': 'Africa',
        'Kerguelen': 'Indian',
        'Wallis': 'Pacific',
        'Yerevan': 'Asia',
        'Guam': 'Pacific',
        'Dominica': 'America',
        'Adelaide': 'Australia',
        'Scoresbysund': 'America',
        'Dubai': 'Asia',
        'Havana': 'America',
        'Norfolk': 'Pacific',
        'Lome': 'Africa',
        'Kampala': 'Africa',
        'Kigali': 'Africa',
        'Ashkhabad': 'Asia',
        'Dublin': 'Europe',
        'Dawson_Creek': 'America',
        'Antananarivo': 'Indian',
        'Tehran': 'Asia',
        'Adak': 'America',
        'Lubumbashi': 'Africa',
        'Accra': 'Africa',
        'Antigua': 'America',
        'Monaco': 'Europe',
        'Mawson': 'Antarctica',
        'Mogadishu': 'Africa',
        'Taipei': 'Asia',
        'St_Thomas': 'America',
        'Pago_Pago': 'Pacific',
        'Jamaica': 'America',
        'Casablanca': 'Africa',
        'Truk': 'Pacific',
        'Cuiaba': 'America',
        'Brisbane': 'Australia',
        'Cairo': 'Africa',
        'Edmonton': 'America',
        'Abidjan': '"Africa',
        'Grand_Turk': 'America',
        'Funafuti': 'Pacific',
        'Marquesas': 'Pacific',
        'Conakry': 'Africa',
        'Windhoek': 'Africa',
        'Paramaribo': 'America',
        'Stanley': 'Atlantic',
        'Macao': 'Asia',
        'Vilnius': 'Europe',
        'Douala': 'Africa',
        'Vladivostok': 'Asia',
        'Caracas': 'America',
        'Harare': 'Africa',
        'Dacca': 'Asia',
        'Tirane': 'Europe',
        'Ouagadougou': 'Africa',
        'Denver': 'America',
        'Damascus': 'Asia',
        'Bermuda': 'Atlantic',
        'St_Vincent': 'America',
        'Canary': 'Atlantic',
        'Sydney': 'Australia',
        'Amman': 'Asia',
        'Dakar': 'Africa',
        'Ujung_Pandang': 'Asia',
        'Bissau': 'Africa',
        'St_Johns': 'America',
        'Vienna': 'Europe',
        'Ndjamena': 'Africa',
        'Seoul': 'Asia',
        'Singapore': 'Asia',
        'Irkutsk': 'Asia',
        'Ulan_Bator': 'Asia',
        'Novosibirsk': 'Asia',
        'Perth': 'Australia',
        'Muscat': 'Asia',
        'Tarawa': 'Pacific',
        'Krasnoyarsk': 'Asia',
        'Wake': 'Pacific',
        'Apia': 'Pacific',
        'Honolulu': 'Pacific',
        'Jakarta': 'Asia',
        'Miquelon': 'America',
        'London': 'Europe',
        'Chatham': 'Pacific',
        'Port_Moresby': 'Pacific',
        'Karachi': 'Asia',
        'Chagos': 'Indian',
        'Bucharest': 'Europe',
        'Majuro': 'Pacific',
        'Brunei': 'Asia',
        'Freetown': 'Africa',
        'Thimbu': 'Asia',
        'Mauritius': 'Indian',
        'Monrovia': 'Africa',
        'Indianapolis': 'America',
        'Libreville': 'Africa',
        'Porto-Novo': 'Africa',
        'Baghdad': 'Asia',
        'Cocos': 'Indian',
        'Kaliningrad': 'Europe',
        'Zurich': 'Europe',
        'Madrid': 'Europe',
        'Baku': 'Asia',
        'Bujumbura': 'Africa',
        'Budapest': 'Europe',
        'Sao_Paulo': 'America',
        'Gambier': 'Pacific',
        'Saipan': 'Pacific',
        'La_Paz': 'America',
        'Jan_Mayen': 'Atlantic',
        'Vientiane': 'Asia',
        'Asmera': 'Africa',
        'Istanbul': 'Europe',
        'Palmer': 'Antarctica',
        'Kuwait': 'Asia',
        'Panama': 'America',
        'Christmas': 'Indian',
        'Cayenne': 'America',
        'Yekaterinburg': 'Asia',
        'Luxembourg': 'Europe',
        'Mazatlan': 'America',
        'Rome': 'Europe',
        'Maseru': 'Africa',
        'Faeroe': 'Atlantic',
        'Gibraltar': 'Europe',
        'Manila': 'Asia',
        'Lisbon': 'Europe',
        'Katmandu': 'Asia',
        'South_Georgia': 'Atlantic',
        'Maldives': 'Indian',
        'Almaty': 'Asia',
        'Aqtobe': 'Asia',
        'Enderbury': 'Pacific',
        'Casey': 'Antarctica',
        'Tongatapu': 'Pacific',
        'Luanda': 'Africa',
        'Aqtau': 'Asia',
        'Niamey': 'Africa',
        'Malta': 'Europe',
        'Pitcairn': 'Pacific',
        'Los_Angeles': 'America',
        'Darwin': 'Australia',
        'Khartoum': 'Africa',
        'Vaduz': 'Europe',
        'Hobart': 'Australia',
        'Manaus': 'America',
        'Asuncion': 'America',
        'Belize': 'America',
        'Kosrae': 'Pacific',
        'Rangoon': 'Asia',
        'Algiers': 'Africa',
        'St_Kitts': 'America',
        'Anadyr': 'Asia',
        'Santo_Domingo': 'America',
        'Tokyo': 'Asia',
        'Galapagos': 'Pacific',
        'Bishkek': 'Asia',
        'Riga': 'Europe',
        'Efate': 'Pacific',
        'Mbabane': 'Africa',
        'Auckland': 'Pacific',
        'Timbuktu': 'Africa',
        'Tunis': 'Africa',
        'Tripoli': 'Africa',
        'Nauru': 'Pacific',
        'Grenada': 'America',
        'Aden': 'Asia',
        'Nairobi': 'Africa',
        'Montreal': 'America',
        'DumontDUrville': 'Antarctica',
        'Port-au-Prince': 'America',
        'Broken_Hill': 'Australia',
        'Reykjavik': 'Atlantic',
        'Port_of_Spain': 'America',
        'Niue': 'Pacific',
        'Copenhagen': 'Europe',
        'Djibouti': 'Africa',
        'Kamchatka': 'Asia',
        'St_Helena': 'Atlantic',
        'Reunion': 'Indian',
        'Halifax': 'America',
        'Lima': 'America',
        'Fiji': 'Pacific',
        'Samara': 'Europe',
        'Barbados': 'America',
        'Saigon': 'Asia',
        'Qatar': 'Asia',
        'Palau': 'Pacific',
        'Curacao': 'America',
        'Chicago': 'America',
        'Brussels': 'Europe',
        'Shanghai': 'Asia',
        'Godthab': 'America',
        'Colombo': 'Asia',
        'Maputo': 'Africa',
        'Rarotonga': 'Pacific',
        'Kabul': 'Asia',
        'Kuala_Lumpur': 'Asia',
        'Lord_Howe': 'Australia',
        'Winnipeg': 'America',
        'Vancouver': 'America',
        'Tallinn': 'Europe',
        'Mahe': 'Indian',
        'Noumea': 'Pacific',
        'Anguilla': 'America',
        'Easter': 'Pacific',
        'Chisinau': 'Europe',
        'Montevideo': 'America',
        'Comoro': 'Indian',
        'Puerto_Rico': 'America',
        'Hong_Kong': 'Asia',
        'Phoenix': 'America',
        'Warsaw': 'Europe',
        'Noronha': 'America',
        'Cayman': 'America',
        'Helsinki': 'Europe',
        'Dushanbe': 'Asia',
        'El_Salvador': 'America',
        'Bangkok': 'Asia',
        'Guadalcanal': 'Pacific',
        'Martinique': 'America',
        'Athens': 'Europe',
        'Nassau': 'America',
        'Guayaquil': 'America',
        'Fakaofo': 'Pacific',
        'New_York': 'America',
        'Mexico_City': 'America',
        'Yakutsk': 'Asia',
        'Thule': 'America',
        'Tahiti': 'Pacific',
        'Mayotte': 'Indian',
        'Anchorage': 'America',
        'Montserrat': 'America',
        'Kiritimati': 'Pacific',
        'Andorra': 'Europe',
        'Gaborone': 'Africa',
        'Managua': 'America',
        'Minsk': 'Europe',
        'McMurdo': 'Antarctica',
        'Porto_Acre': 'America',
        'Guyana': 'America',
        'Magadan': 'Asia',
        'St_Lucia': 'America',
        'Guadeloupe': 'America',
        'Tbilisi': 'Asia',
        'Tijuana': 'America',
        'Jerusalem': 'Asia',
        'Tashkent': 'Asia',
        'Belgrade': 'Europe',
        'Riyadh': 'Asia',
        'Bogota': 'America',
        'Prague': 'Europe',
        'Sofia': 'Europe',
        'Jayapura': 'Asia',
        'Tortola': 'America',
        'Lagos': 'Africa',
        'Nouakchott': 'Africa',
        'Blantyre': 'Africa',
        'Pyongyang': 'Asia',
        'Amsterdam': 'Europe',
        'Costa_Rica': 'America',
        'Lusaka': 'Africa',
        'Moscow': 'Europe',
        'Stockholm': 'Europe'
    };

    if (doc.user) {
        if (doc.user.time_zone != '') {
            if(doc.user.time_zone in time_zones) {
                emit(time_zones[doc.user.time_zone], 1);
            } else {
                emit('Unknown', 1);
            }
        } else {
            emit('Unspecified', 1);
        }
    }
}