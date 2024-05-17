
class InfiniteScrollPagination:
    def __init__(self, data, limit, has_more, tool_status=None, response_status=None):
        self.data = data
        self.limit = limit
        self.has_more = has_more
        self.response_status = response_status 
        self.tool_status = tool_status
