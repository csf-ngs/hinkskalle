<template>
  <div class="collections">
    <top-bar title="Collections"></top-bar>
    <v-container>
      <v-row>
        <v-col cols="12" md="10" offset-md="1">
          <v-data-iterator
            id="collections"
            :items="collections"
            :search="localState.search"
            :loading="loading">
            <template v-slot:header>
              <v-toolbar flat>
                <v-text-field id="search" v-model="localState.search" prepend-icon="mdi-magnify" label="Search..." single-line hide-details></v-text-field>
                <v-spacer></v-spacer>
                <v-dialog v-model="localState.showEdit" max-width="700px">
                  <template v-slot:activator="{ on, attrs }">
                    <v-btn v-if="entity && entity.canEdit(currentUser)" id="create-collection" color="primary darken-1" text v-bind="attrs" v-on="on">Create Collection</v-btn>
                  </template>
                  <v-card>
                    <v-card-title class="headline">{{editTitle}}</v-card-title>
                    <v-card-text>
                      <v-container>
                        <v-row>
                          <v-col cols="12">
                            <hsk-text-input 
                              id="name"
                              label="Name"
                              field="name"
                              :obj="localState.editItem"
                              :readonly="!!localState.editItem.id"
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
                              type="yesno"
                              label="Private"
                              field="private"
                              :obj="localState.editItem"
                              @updated="localState.editItem=$event"></hsk-text-input>
                          </v-col>
                        </v-row>
                        <v-row>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created"
                              :static-value="localState.editItem.createdAt | moment('YYYY-MM-DD HH:mm')"
                              ></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Created By"
                              :static-value="localState.editItem.createdBy"></hsk-text-input>
                          </v-col>
                          <v-col cols="12" md="4">
                            <hsk-text-input
                              label="Updated"
                              :static-value="updatedAt"
                              ></hsk-text-input>
                          </v-col>
                        </v-row>
                      </v-container>
                    </v-card-text>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary accent-1" text @click="closeEdit">Mabye not today.</v-btn>
                      <v-btn id="save" color="primary darken-1" text @click="save">Save It!</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-dialog v-model="localState.showDelete" max-width="500px">
                  <v-card>
                    <v-card-title class="headline">You really want to kill it?</v-card-title>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <v-btn color="secondary darken-1" text @click="closeDelete">Let mercy rule.</v-btn>
                      <v-btn color="warning accent-1" text @click="deleteCollectionConfirm">Get it out of my sight.</v-btn>
                    </v-card-actions>
                  </v-card>
                </v-dialog>
                <v-btn id="refresh" color="primary darken-1" text @click="loadCollections()"><v-icon>mdi-refresh</v-icon></v-btn>
              </v-toolbar>
            </template>
            <template v-slot:default="props">
              <v-row>
                <v-col v-for="item in props.items" :key="item.id"
                  cols="12" md="6">
                  <v-card class="collection">
                    <router-link :to="{ name: 'Containers', params: { entity: item.entityName, collection: item.name } }" class="text-decoration-none">
                      <v-card-title class="headline">
                        <v-icon v-if="item.private">mdi-eye-off</v-icon>
                        {{item.name}}
                        ({{item.size}} {{item.size | pluralize('container')}})
                      </v-card-title>
                    </router-link>
                    <v-divider></v-divider>
                    <v-list dense>
                      <v-list-item two-lines>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.description}}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                      <v-list-item two-lines>
                        <v-list-item-content>
                          <v-list-item-title>
                            {{item.createdAt | moment('YYYY-MM-DD HH:mm')}} | {{item.createdBy}}
                          </v-list-item-title>
                          <v-list-item-subtitle>
                            Created
                          </v-list-item-subtitle>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                    <v-card-actions>
                      <v-spacer></v-spacer>
                      <template v-if="item.canEdit(currentUser)">
                        <v-icon small class="mr-1" @click="editCollection(item)">mdi-pencil</v-icon>
                        <v-icon small @click="deleteCollection(item)">mdi-delete</v-icon>
                      </template>
                      <template v-else>
                        <v-icon small>mdi-cancel</v-icon>
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
import { Collection, Entity, User } from '../store/models';
import Vue from 'vue';
import { DataTableHeader } from 'vuetify';

import { clone as _clone } from 'lodash';
import moment from 'moment';

interface State {
  search: string;
  editItem: Collection;
  showEdit: boolean;
  showDelete: boolean;
}

function defaultItem(): Collection {
  const item = new Collection();
  item.createdAt = new Date();
  return item;
}

export default Vue.extend({
  name: 'Collections',
  mounted() {
    this.loadCollections();
  },
  data: (): { headers: DataTableHeader[]; localState: State } => ({
    headers: [
      { text: 'Id', value: 'id', sortable: true, filterable: false, width: '7%' },
      { text: 'Name', value: 'name', sortable: true, filterable: true, width: '15%' },
      { text: 'Description', value: 'description', sortable: true, filterable: true, width: '' },
      { text: 'Size', value: 'size', sortable: true, filterable: false, width: '8%', },
      { text: 'Created', value: 'createdAt', sortable: true, filterable: false, width: '12%', },
      { text: 'Actions', value: 'actions', sortable: false, filterable: false, width: '5%', },
    ],
    localState: {
      search: '',
      showEdit: false,
      showDelete: false,
      editItem: defaultItem(),
    },
  }),
  computed: {
    collections(): Collection[] {
      return this.$store.getters['collections/list'];
    },
    loading(): boolean {
      return this.$store.getters['collections/status']==='loading';
    },
    editTitle(): string {
      return this.localState.editItem.id ? 'Edit Collection' : 'New Collection';
    },
    updatedAt(): string {
      return this.localState.editItem.updatedAt ?
        moment(this.localState.editItem.updatedAt).format('YYYY-MM-DD HH:mm') :
        '-';
    },
    entity(): Entity {
      return this.$store.getters['collections/currentEntity'];
    },
    currentUser(): User {
      return this.$store.getters.currentUser;
    }
  },
  watch: {
    $route() {
      this.loadCollections();
    },
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
    loadCollections() {
      this.$store.dispatch('collections/list', this.$route.params.entity)
        .catch(err => this.$store.commit('snackbar/showError', err));
    },
    editCollection(collection: Collection) {
      this.localState.editItem = _clone(collection);
      this.localState.showEdit = true;
    },
    deleteCollection(collection: Collection) {
      this.localState.editItem = _clone(collection);
      this.localState.showDelete = true;
    },
    deleteCollectionConfirm() {
      this.$store.dispatch('collections/delete', this.localState.editItem)
        .then(() => this.$store.commit('snackbar/showSuccess', "It's gone!"))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeDelete();
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
        'collections/update' : 'collections/create';
      if (this.$route.params.entity) {
        this.localState.editItem.entityName = this.$route.params.entity;
      }
      this.$store.dispatch(action, this.localState.editItem)
        .then(upd => this.$store.commit('snackbar/showSuccess', 'Yay!'))
        .catch(err => this.$store.commit('snackbar/showError', err));
      this.closeEdit();
    },
  }
});
</script>