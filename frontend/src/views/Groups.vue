<template>
  <div class="groups">
    <top-bar title="Groups"></top-bar>
    <v-container>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-iterator
            id="groups"
            :items="groups"
            :search="localState.search"
            :sort-by="localState.sortBy"
            :sort-desc="localState.sortDesc"
            :loading="loading">
            <template v-slot:header>
              <v-toolbar flat>
                <v-text-field id="search"
                  v-model="localState.search"
                  prepend-inner-icon="mdi-magnify"
                  label="Search..."
                  single-line outlined dense hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-select class="mr-1"
                  v-model="localState.sortBy" 
                  label="Sort..."
                  hide-details outlined dense
                  :items="sortKeys"
                  item-text="desc"
                  item-value="key"
                  prepend-inner-icon="mdi-sort"></v-select>
                <v-btn-toggle dense active-class="green--text" borderless
                  v-model="localState.sortDesc" mandatory>
                  <v-btn :value="true"><v-icon>mdi-sort-descending</v-icon></v-btn>
                  <v-btn :value="false"><v-icon>mdi-sort-ascending</v-icon></v-btn>
                </v-btn-toggle>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="700px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn 
                      id="create-group" 
                      dense depressed
                      v-bind="attrs" v-on="on">Create Group</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-form v-model="localState.editValid">
                        <v-row>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="name"
                              label="Name"
                              field="name"
                              :obj="localState.editItem"
                              :readonly="!!localState.editItem.id"
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="description"
                              label="Description"
                              field="description"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="email"
                              label="Email"
                              field="email"
                              :obj="localState.editItem"
                              required
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="6">
                            <hsk-text-input
                              id="quota"
                              label="Quota (0 = unlimited)" 
                              field="prettyQuota" 
                              :obj="localState.editItem" 
                              :readonly="!currentUser.isAdmin"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="6">
                            <hsk-text-input label="Used Quota" :static-value="localState.editItem.used_quota | prettyBytes"></hsk-text-input>
                          </v-col>
                        </v-row>
                        <v-row v-if="localState.editItem.id">
                          <v-col cols="12" md="4">
                            <hsk-user-input 
                              label="Owner"
                              :readonly="!currentUser.isAdmin"
                              v-model="localState.editItem.createdBy"
                              ></hsk-user-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created"
                              :static-value="localState.editItem.createdAt | prettyDateTime"
                              ></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Updated"
                              :static-value="localState.editItem.updatedAt | prettyDateTime"
                              ></hsk-text-input>
                          </v-col>
                        </v-row>
                        </v-form>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn color="primary darken-1" :disabled="!localState.editValid" text @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kill it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-spacer></v-spacer>
                <v-btn 
                  id="refresh" 
                  class="ml-2"
                  dense depressed 
                  @click="loadGroups()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <template v-slot:default="props">
              <v-row>
                <v-col v-for="item in props.items" :key="item.id" cols="12" md="6">
                  <v-card class="group">
                    <router-link :to="{ name: 'GroupDetails', params: { group: item.name } }" class="text-decoration-none">
                      <v-card-title class="headline">
                        <v-icon>{{ roleIcon(item) }}</v-icon>
                        {{item.name}}
                      </v-card-title>
                    </router-link>
                    <v-divider></v-divider>
                    <v-list dense>
                      <v-list-item>
                        <v-list-item-content>
                          <v-list-item-title>
                            You are: {{ item.getRole(currentUser) }}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-content>
                          <v-list-item-title class="d-flex justify-space-between">
                            <div>
                              {{item.users.length}} {{item.users.length | pluralize('user')}}
                            </div>
                            <div>
                              {{(item.used_quota ||0) | prettyBytes()}}
                              <span v-if="item.quota === 0">/ &infin;</span>
                              <span v-else>/ {{item.quota | prettyBytes()}}</span>
                            </div>
                            <div>
                              <router-link :to="{ name: 'EntityCollections', params: { entity: item.entityRef } }" class="text-decoration-none">
                                <v-icon>mdi-folder-multiple</v-icon> {{item.collections}} {{item.collections | pluralize('collection')}}
                              </router-link>
                            </div>
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.description || '-'}}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-lines>
                        <v-list-item-content>
                          <v-list-item-title class="d-flex justify-space-between">
                            <div>
                              {{item.createdAt | prettyDateTime}} | {{item.createdBy}}
                            </div>
                            <div>
                              {{item.updatedAt | prettyDateTime}} 
                            </div>
                          </v-list-item-title>
                          <v-list-item-subtitle class="d-flex justify-space-between">
                            <div>Created</div>
                            <div>Updated</div>
                          </v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <template v-if="item.canEdit">
                        <v-icon small class="mr-1" @click="editGroup(item)">mdi-pencil</v-icon>
                        <v-icon small @click="deleteGroup(item)">md-delete</v-icon>
                      </template>
                    </v-card-actions>
                  </v-card>
                </v-col>
              </v-row>
            </template>
          </v-data-iterator>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>
<script lang="ts">
import Vue from 'vue';
import { checkName, Group, GroupRoles, User } from '../store/models';
import { clone as _clone } from 'lodash';
import UserInput from '@/components/UserInput.vue';
import store from '@/store';

interface State {
  editItem: Group;
  showEdit: boolean;
  editValid: boolean;
  showDelete: boolean;
  search: string,
  sortBy: string;
  sortDesc: boolean;
}

function defaultItem(): Group {
  const item = new Group();
  item.createdAt = new Date();
  item.quota = store.getters.config?.default_group_quota;
  return item;
}

export default Vue.extend({
  name: 'HskGroups',
  components: { 'hsk-user-input': UserInput },
  mounted() {
    this.loadGroups();
  },
  data: (): { localState: State; sortKeys: { key: string; desc: string }[] } => ({
    localState: {
      showEdit: false,
      showDelete: false,
      editItem: defaultItem(),
      editValid: true,
      search: '',
      sortBy: 'name',
      sortDesc: false,
    },
    sortKeys: [
      { key: 'name', desc: 'Name' },
      { key: 'used_quota', desc: 'Size' },
      { key: 'createdAt', desc: 'Create Date' },
      { key: 'updatedAt', desc: 'Last Updated' },
    ]
  }),
  computed: {
    groups(): Group[] {
      return this.$store.getters['groups/list'];
    },
    loading(): boolean {
      return this.$store.getters['groups/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit Group' : 'New Group';
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    },
  },
  watch: {
    'localState.showEdit': function showEdit(val) {
      if (!val) {
        this.closeEdit();
      }
    },
    'localState.showDelete': function showDelete(val) {
      if (!val) {
        this.closeDelete();
      }
    },
  },
  methods: {
    loadGroups() {
      this.$store.dispatch('groups/list')
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    editGroup(group: Group) {
      this.localState.editItem = _clone(group);
      this.localState.showEdit = true;
    },
    deleteGroup(group: Group) {
      this.localState.editItem = _clone(group);
      this.localState.showDelete = true;
    },
    deleteConfirm() {
      this.$store.dispatch('groups/delete', this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', "It's gone!"))
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    closeEdit() {
      this.localState.showEdit = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    closeDelete() {
      this.localState.showDelete = false;
      this.$nextTick(() => {
        this.localState.editItem = defaultItem();
      });
    },
    save() {
      const action = this.localState.editItem.id ? 
        'groups/update' : 'groups/create';
      this.$store.dispatch(action, this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', 'Yay!'))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeEdit();
    },
    checkName(name: string): string | boolean {
      return checkName(name);
    },
    roleIcon(group: Group): string {
      const role = group.getRole(this.currentUser);
      switch(role) {
        case GroupRoles.admin:
          return 'mdi-book-account';
        case GroupRoles.contributor:
          return 'mdi-book-plus';
        case GroupRoles.readonly:
          return 'mdi-book-lock';
        default:
          return 'mdi-head-question';
      }
    }
  }
});

</script>