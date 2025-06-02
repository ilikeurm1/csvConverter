# csv converter

## cfg file

The config file should look like this (`detailed_plots` is not to be changed):

```json
{
    "detailed_plots": [
        {
            "file": "Test3.csv", // filename
            "from": "17:31:00",  // starting time
            "length": "06:15"    // duration in hours
        },
        {
            "file": "Test6.csv",
            "from": "17:02:00", 
            "length": "10:30"
        },
        {
            "file": "Test6.csv",
            "from": "13:02:00", 
            "length": "04:00"
        }
    ]
}
```
