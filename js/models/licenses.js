import { List } from "models/base";

export class Licenses extends List {
  constructor(options) {
    super(options);
    this.$options.ns = "datasets";
    this.$options.fetch = "list_licenses";
  }

  on_fetched(data) {
    data.obj = this.sortLicensesData(data.obj);
    super.on_fetched(data);
  }

  sortLicensesData(data) {
    // https://gitlab.geoportail.lu/geoportail/migration-data-public-lu/-/issues/123
    const sortedLicenses = [];
    const order = [
      "cc-zero",
      "cc-by",
      "cc-by-sa",
      "odc-pddl",
      "odc-by",
      "odc-odbl",
      "other-pd",
      "other-at",
      "other-open",
    ];

    // Add sorted licenses
    for (const value of order) {
      const license = data.find((license) => license.id === value);
      if (license) {
        sortedLicenses.push(license);
      } 
    }

    // Add not sorted yet licenses
    const addedIds = sortedLicenses.map((license) => license.id);
    for (const license of data) {
      if (!addedIds.includes(license.id)) {
        sortedLicenses.push(license);
      }
    }
    return sortedLicenses;
  }
}

export var licenses = new Licenses().fetch();
export default licenses;
