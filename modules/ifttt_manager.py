import requests


class WebHooks_IFTTT:
    def __init__(self, key):
        self.key = key

    def send(self, channel, value_1=None, value_2=None, value_3=None):
        data = {
            "value1": value_1,
            "value2": value_2,
            "value3": value_3
        }
        requests.post("https://maker.ifttt.com/trigger/{}/with/key/{}".format(channel, self.key), data=data)


if __name__ == '__main__':
    ifttt = WebHooks_IFTTT('ckcorpj6ouQG_nn2YGYyQn')
    ifttt.send('halfway')
