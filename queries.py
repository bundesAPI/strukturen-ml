from gql import gql

UPDATE_ORG_CHART = gql(
    """
    mutation updateOrgChart($orgChartId: ID!, $status: OrgChartStatusChoices!, $rawSource: JSONString!) {
  updateOrgChart(orgChartId: $orgChartId, status: $status, rawSource: $rawSource) {
    orgChart {
      id
    }
  }
}
"""
)

ORG_CHART_QUERY = gql(
    """
    query getOrgChart($id: ID!){
      orgChart(id: $id) {
        id
        document
        status
        rawSource
        documentHash
        createdAt
      }
    }
    """
)
