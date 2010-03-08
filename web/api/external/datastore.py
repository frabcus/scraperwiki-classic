import connection

class Datastore:

    #properties
    connection = False

    #constructor
    def __init__(self):
        self.connection = connection.Connection()

    def postcode_lookup (self, postcode, country_code):
        return_val = None
        try:
            c = self.connection.cursor()
            sql = " select AsText(location), postcode, country_code from postcode_lookup where postcode = %s and country_code = %s"
            c.execute(sql, (postcode, country_code,))
            result = c.fetchone()
            if result:
                latlng = result[0].replace('POINT(', '').replace(')', '').split(' ')
                return_val = {'lat': latlng[0], 'lng': latlng[1], 'postcode': result[1], 'country_code': result[2]}
        except:
            return_val = None

        return return_val

